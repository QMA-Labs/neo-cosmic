import sqlite3

import pytest

from neo.drive import DriveManager, VaultArchive


def test_encrypted_archive_round_trip_and_wrong_password(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "memory.txt").write_text("NEO secret", encoding="utf-8")
    archive = VaultArchive.encrypt_directory(
        source, tmp_path / "backup.neo", "correct horse battery"
    )
    assert b"NEO secret" not in archive.read_bytes()
    with pytest.raises(ValueError):
        VaultArchive.decrypt_archive(archive, tmp_path / "wrong", "wrong password value")
    restored = VaultArchive.decrypt_archive(archive, tmp_path / "restored", "correct horse battery")
    assert (restored / "memory.txt").read_text() == "NEO secret"


def test_migration_manifest_and_source_preserved(tmp_path) -> None:
    source = tmp_path / "NEO"
    source.mkdir()
    (source / "brain.db").write_bytes(b"brain")
    (source / "profiles").mkdir()
    (source / "profiles" / "owner.json").write_text("{}")
    report = DriveManager(source).migrate(tmp_path / "NEW-NEO")
    assert report.verified and report.files == 2
    assert (source / "brain.db").exists()
    assert (tmp_path / "NEW-NEO" / "brain.db").read_bytes() == b"brain"


def test_sqlite_consistent_backup(tmp_path) -> None:
    root = tmp_path / "neo"
    root.mkdir()
    database = root / "neo.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE test(value TEXT)")
        connection.execute("INSERT INTO test VALUES('safe')")
    backup = DriveManager(root).backup_database(database, tmp_path / "backup.sqlite3")
    with sqlite3.connect(backup) as connection:
        assert connection.execute("SELECT value FROM test").fetchone()[0] == "safe"


def test_rejects_short_password_and_nested_migration(tmp_path) -> None:
    source = tmp_path / "neo"
    source.mkdir()
    with pytest.raises(ValueError):
        VaultArchive.encrypt_directory(source, tmp_path / "x.neo", "short")
    with pytest.raises(ValueError):
        DriveManager(source).migrate(source / "nested")
