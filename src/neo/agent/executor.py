from __future__ import annotations

import os
import platform
import shutil
import subprocess
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from neo.agent.permissions import PermissionStore
from neo.memory import MemoryKind, MemoryStore


class ActionType(StrEnum):
    WRITE_FILE = "write_file"
    MOVE_FILE = "move_file"
    COPY_FILE = "copy_file"
    OPEN_APP = "open_app"
    GIT_STATUS = "git_status"
    DOCKER_PS = "docker_ps"
    OLLAMA_LIST = "ollama_list"
    SERVICE_STATUS = "service_status"
    TASK_LIST = "task_list"


@dataclass(frozen=True, slots=True)
class ActionRequest:
    type: ActionType
    target: str | None = None
    arguments: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class ActionResult:
    id: str
    action: str
    success: bool
    message: str
    verified: bool
    undo_available: bool
    output: str | None = None


class ActionExecutor:
    """Typed, permission-gated executor. Never invokes a shell or accepts raw commands."""

    READ_ONLY = {
        ActionType.GIT_STATUS,
        ActionType.DOCKER_PS,
        ActionType.OLLAMA_LIST,
        ActionType.SERVICE_STATUS,
        ActionType.TASK_LIST,
    }

    def __init__(self, memory: MemoryStore, backup_dir: Path) -> None:
        self.memory = memory
        self.permissions = PermissionStore(memory)
        self.backup_dir = backup_dir
        backup_dir.mkdir(parents=True, exist_ok=True)

    def preview(self, request: ActionRequest) -> str:
        target = f" target={request.target}" if request.target else ""
        return f"{request.type.value}{target} arguments={request.arguments or {}}"

    def execute(self, request: ActionRequest) -> ActionResult:
        target = Path(request.target).expanduser().resolve() if request.target else None
        if not self.permissions.authorize(request.type.value, target):
            raise PermissionError(f"permission required: {self.preview(request)}")
        action_id = uuid.uuid4().hex
        try:
            if request.type == ActionType.WRITE_FILE:
                result = self._write(action_id, target, request.arguments or {})
            elif request.type == ActionType.MOVE_FILE:
                result = self._move(action_id, target, request.arguments or {})
            elif request.type == ActionType.COPY_FILE:
                result = self._copy(action_id, target, request.arguments or {})
            elif request.type == ActionType.OPEN_APP:
                result = self._open(action_id, target)
            else:
                result = self._fixed_command(action_id, request)
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            result = ActionResult(action_id, request.type.value, False, str(exc), False, False)
        self.memory.set(
            f"agent.audit.{action_id}",
            {
                "request": asdict(request),
                "result": asdict(result),
                "at": datetime.now(UTC).isoformat(),
            },
            kind=MemoryKind.CORE,
            protected=True,
            source="windows-agent",
        )
        return result

    def undo(self, action_id: str) -> ActionResult:
        entry = self.memory.get(f"agent.undo.{action_id}")
        if not entry:
            raise KeyError("no undo record")
        data = entry.value
        source, destination = Path(data["source"]), Path(data["destination"])
        if data["operation"] == "restore":
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        elif data["operation"] == "move_back":
            shutil.move(source, destination)
        elif data["operation"] == "delete_created":
            source.unlink(missing_ok=True)
        else:
            raise ValueError("unknown undo operation")
        verified = (
            destination.exists() if data["operation"] != "delete_created" else not source.exists()
        )
        return ActionResult(action_id, "undo", verified, "undo completed", verified, False)

    def _write(
        self, action_id: str, target: Path | None, arguments: dict[str, Any]
    ) -> ActionResult:
        if target is None:
            raise ValueError("write_file requires target")
        content = str(arguments.get("content", ""))
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            backup = self.backup_dir / f"{action_id}.bak"
            shutil.copy2(target, backup)
            self._undo(action_id, "restore", backup, target)
        else:
            self._undo(action_id, "delete_created", target, target)
        temporary = target.with_name(f".{target.name}.{action_id}.tmp")
        temporary.write_text(content, encoding="utf-8")
        os.replace(temporary, target)
        verified = target.read_text(encoding="utf-8") == content
        return ActionResult(action_id, "write_file", verified, "file written", verified, True)

    def _move(self, action_id: str, target: Path | None, arguments: dict[str, Any]) -> ActionResult:
        if target is None or "destination" not in arguments:
            raise ValueError("move_file requires source and destination")
        destination = Path(arguments["destination"]).expanduser().resolve()
        if destination.exists():
            raise FileExistsError(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(target, destination)
        self._undo(action_id, "move_back", destination, target)
        verified = destination.exists() and not target.exists()
        return ActionResult(action_id, "move_file", verified, "file moved", verified, True)

    def _copy(self, action_id: str, target: Path | None, arguments: dict[str, Any]) -> ActionResult:
        if target is None or "destination" not in arguments:
            raise ValueError("copy_file requires source and destination")
        destination = Path(arguments["destination"]).expanduser().resolve()
        if destination.exists():
            raise FileExistsError(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, destination)
        self._undo(action_id, "delete_created", destination, destination)
        verified = destination.exists() and destination.stat().st_size == target.stat().st_size
        return ActionResult(action_id, "copy_file", verified, "file copied", verified, True)

    @staticmethod
    def _open(action_id: str, target: Path | None) -> ActionResult:
        if target is None:
            raise ValueError("open_app requires an executable target")
        subprocess.Popen([str(target)], shell=False, close_fds=True)
        return ActionResult(action_id, "open_app", True, "application launched", True, False)

    def _fixed_command(self, action_id: str, request: ActionRequest) -> ActionResult:
        command = self._command_for(request)
        completed = subprocess.run(command, shell=False, capture_output=True, text=True, timeout=30)
        output = (completed.stdout + completed.stderr)[-20_000:]
        success = completed.returncode == 0
        return ActionResult(
            action_id, request.type.value, success, "command completed", success, False, output
        )

    @staticmethod
    def _command_for(request: ActionRequest) -> list[str]:
        args = request.arguments or {}
        if request.type == ActionType.GIT_STATUS:
            return ["git", "-C", str(Path(request.target or ".").resolve()), "status", "--short"]
        if request.type == ActionType.DOCKER_PS:
            return ["docker", "ps", "--format", "{{json .}}"]
        if request.type == ActionType.OLLAMA_LIST:
            return ["ollama", "list"]
        if request.type == ActionType.SERVICE_STATUS and platform.system() == "Windows":
            name = str(args.get("name", ""))
            if not name or any(
                char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
                for char in name
            ):
                raise ValueError("invalid service name")
            return ["sc.exe", "query", name]
        if request.type == ActionType.TASK_LIST and platform.system() == "Windows":
            return ["schtasks.exe", "/Query", "/FO", "CSV"]
        raise ValueError("action is unavailable on this platform")

    def _undo(self, action_id: str, operation: str, source: Path, destination: Path) -> None:
        self.memory.set(
            f"agent.undo.{action_id}",
            {"operation": operation, "source": str(source), "destination": str(destination)},
            kind=MemoryKind.TEMPORARY,
            protected=True,
            source="windows-agent",
            ttl_seconds=604_800,
        )
