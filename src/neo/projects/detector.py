from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from neo.memory import MemoryKind, MemoryStore


@dataclass(frozen=True, slots=True)
class ProjectProfile:
    id: str
    name: str
    path: str
    stack: str
    markers: tuple[str, ...]
    run_commands: tuple[str, ...]
    test_commands: tuple[str, ...]
    dependencies: tuple[str, ...]
    confidence: float
    detected_at: str


class ProjectDetector:
    MARKERS = {
        "pyproject.toml": "python",
        "requirements.txt": "python",
        "package.json": "node",
        "Cargo.toml": "rust",
        "go.mod": "go",
        "pom.xml": "java-maven",
        "build.gradle": "java-gradle",
    }

    def __init__(self, memory: MemoryStore) -> None:
        self.memory = memory

    def discover(self, roots: tuple[Path, ...], max_depth: int = 6) -> list[ProjectProfile]:
        found: dict[Path, set[str]] = {}
        for root in roots:
            root = root.expanduser().resolve()
            if not root.is_dir():
                continue
            for current, dirs, files in os.walk(root):
                current_path = Path(current)
                try:
                    depth = len(current_path.relative_to(root).parts)
                except ValueError:
                    continue
                dirs[:] = [
                    d for d in dirs if d not in {".git", ".venv", "node_modules", "target", "build"}
                ]
                if depth >= max_depth:
                    dirs[:] = []
                markers = {
                    name
                    for name in files
                    if name in self.MARKERS or name.endswith((".sln", ".csproj"))
                }
                if markers:
                    found.setdefault(current_path, set()).update(markers)
        profiles = [self.inspect(path, tuple(sorted(markers))) for path, markers in found.items()]
        for profile in profiles:
            self.memory.set(
                f"projects.profile.{profile.id}",
                asdict(profile),
                kind=MemoryKind.LEARNED,
                confidence=profile.confidence,
                source="project-detector",
                evidence={"markers": profile.markers},
            )
            self._write_skill(profile)
        return profiles

    def inspect(self, path: Path, markers: tuple[str, ...] | None = None) -> ProjectProfile:
        path = path.resolve()
        markers = markers or tuple(name for name in self.MARKERS if (path / name).is_file())
        stack = self._stack(markers)
        run, test, dependencies = self._commands_and_dependencies(path, stack)
        project_id = hashlib.sha256(str(path).encode()).hexdigest()[:20]
        return ProjectProfile(
            project_id,
            path.name,
            str(path),
            stack,
            markers,
            run,
            test,
            dependencies,
            0.95 if markers else 0.3,
            datetime.now(UTC).isoformat(),
        )

    def _write_skill(self, profile: ProjectProfile) -> None:
        self.memory.set(
            f"skills.project.{profile.id}",
            {
                "project_id": profile.id,
                "working_directory": profile.path,
                "run": profile.run_commands,
                "test": profile.test_commands,
                "safety": "commands require user confirmation until learned as trusted",
            },
            kind=MemoryKind.LEARNED,
            confidence=profile.confidence,
            source="project-detector",
        )

    @classmethod
    def _stack(cls, markers: tuple[str, ...]) -> str:
        stacks = {cls.MARKERS[name] for name in markers if name in cls.MARKERS}
        if any(name.endswith((".sln", ".csproj")) for name in markers):
            stacks.add("dotnet")
        return "+".join(sorted(stacks)) if stacks else "unknown"

    @staticmethod
    def _commands_and_dependencies(
        path: Path, stack: str
    ) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
        if "python" in stack:
            return ("python -m neo",), ("pytest",), ProjectDetector._python_dependencies(path)
        if "node" in stack:
            package = ProjectDetector._json(path / "package.json")
            scripts = package.get("scripts", {})
            run = tuple(f"npm run {name}" for name in ("dev", "start") if name in scripts)
            test = ("npm test",) if "test" in scripts else ()
            deps = tuple(
                sorted({*package.get("dependencies", {}), *package.get("devDependencies", {})})
            )
            return run, test, deps
        defaults = {
            "rust": (("cargo run",), ("cargo test",)),
            "go": (("go run .",), ("go test ./...",)),
            "dotnet": (("dotnet run",), ("dotnet test",)),
            "java-maven": (("mvn package",), ("mvn test",)),
            "java-gradle": (("gradle build",), ("gradle test",)),
        }
        run, test = defaults.get(stack, ((), ()))
        return run, test, ()

    @staticmethod
    def _python_dependencies(path: Path) -> tuple[str, ...]:
        requirements = path / "requirements.txt"
        if not requirements.is_file():
            return ()
        return tuple(
            line.strip()
            for line in requirements.read_text(encoding="utf-8", errors="replace").splitlines()
            if line.strip() and not line.lstrip().startswith(("#", "-"))
        )

    @staticmethod
    def _json(path: Path) -> dict[str, Any]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
