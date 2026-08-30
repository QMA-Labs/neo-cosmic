from pathlib import Path

import pytest

from neo.agent import ActionExecutor, ActionRequest, ActionType, PermissionScope
from neo.memory import MemoryStore


def executor(tmp_path: Path) -> ActionExecutor:
    return ActionExecutor(MemoryStore(tmp_path / "memory.sqlite3"), tmp_path / "backups")


def test_action_requires_permission(tmp_path) -> None:
    service = executor(tmp_path)
    with pytest.raises(PermissionError):
        service.execute(
            ActionRequest(ActionType.WRITE_FILE, str(tmp_path / "file.txt"), {"content": "x"})
        )


def test_write_verify_and_undo_new_file(tmp_path) -> None:
    service = executor(tmp_path)
    target = tmp_path / "folder" / "file.txt"
    service.permissions.grant("write_file", PermissionScope.ONCE)
    result = service.execute(
        ActionRequest(ActionType.WRITE_FILE, str(target), {"content": "hello"})
    )
    assert result.success and result.verified and result.undo_available
    assert target.read_text() == "hello"
    undo = service.undo(result.id)
    assert undo.verified and not target.exists()
    with pytest.raises(PermissionError):
        service.execute(ActionRequest(ActionType.WRITE_FILE, str(target), {"content": "again"}))


def test_folder_permission_and_restore_existing_file(tmp_path) -> None:
    service = executor(tmp_path)
    folder = tmp_path / "project"
    folder.mkdir()
    target = folder / "config.txt"
    target.write_text("old")
    service.permissions.grant("write_file", PermissionScope.FOLDER, str(folder))
    result = service.execute(ActionRequest(ActionType.WRITE_FILE, str(target), {"content": "new"}))
    assert target.read_text() == "new"
    service.undo(result.id)
    assert target.read_text() == "old"


def test_move_refuses_overwrite(tmp_path) -> None:
    service = executor(tmp_path)
    source, destination = tmp_path / "a", tmp_path / "b"
    source.write_text("a")
    destination.write_text("b")
    service.permissions.grant("move_file", PermissionScope.ONCE)
    result = service.execute(
        ActionRequest(ActionType.MOVE_FILE, str(source), {"destination": str(destination)})
    )
    assert result.success is False
    assert source.exists() and destination.read_text() == "b"
