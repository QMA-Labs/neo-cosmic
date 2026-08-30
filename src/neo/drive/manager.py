from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import sqlite3
import tempfile
import zipfile
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

MAGIC = b"NEOARCHIVE1\n"


@dataclass(frozen=True, slots=True)
class StorageReport:
    root: str
    total_gb: float
    used_gb: float
    free_gb: float
    neo_bytes: int
    status: str


@dataclass(frozen=True, slots=True)
class MigrationReport:
    source: str
    destination: str
    files: int
    bytes_copied: int
    verified: bool
    manifest: str


class VaultArchive:
    """Password-encrypted .neo archive using scrypt and AES-256-GCM."""

    @staticmethod
    def encrypt_directory(source: Path, destination: Path, password: str) -> Path:
        if len(password) < 12:
            raise ValueError("archive password must contain at least 12 characters")
        payload = VaultArchive._zip_bytes(source)
        salt, nonce = os.urandom(16), os.urandom(12)
        key = VaultArchive._derive(password, salt)
        header = {
            "version": 1,
            "cipher": "AES-256-GCM",
            "kdf": "scrypt-n16384-r8-p1",
            "salt": salt.hex(),
            "nonce": nonce.hex(),
            "created_at": datetime.now(UTC).isoformat(),
        }
        header_bytes = json.dumps(header, separators=(",", ":")).encode()
        ciphertext = AESGCM(key).encrypt(nonce, payload, header_bytes)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_bytes(
            MAGIC + len(header_bytes).to_bytes(4, "big") + header_bytes + ciphertext
        )
        os.replace(temporary, destination)
        return destination

    @staticmethod
    def decrypt_archive(archive: Path, destination: Path, password: str) -> Path:
        raw = archive.read_bytes()
        if not raw.startswith(MAGIC):
            raise ValueError("not a NEO archive")
        offset = len(MAGIC)
        header_length = int.from_bytes(raw[offset : offset + 4], "big")
        header_start = offset + 4
        header_bytes = raw[header_start : header_start + header_length]
        header = json.loads(header_bytes)
        try:
            payload = AESGCM(VaultArchive._derive(password, bytes.fromhex(header["salt"]))).decrypt(
                bytes.fromhex(header["nonce"]), raw[header_start + header_length :], header_bytes
            )
        except InvalidTag as exc:
            raise ValueError("wrong password or corrupted archive") from exc
        destination.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(payload)) as archive_zip:
            VaultArchive._safe_extract(archive_zip, destination)
        return destination

    @staticmethod
    def _derive(password: str, salt: bytes) -> bytes:
        return Scrypt(salt=salt, length=32, n=2**14, r=8, p=1).derive(password.encode("utf-8"))

    @staticmethod
    def _zip_bytes(source: Path) -> bytes:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for path in sorted(source.rglob("*")):
                if path.is_file() and not path.is_symlink():
                    archive.write(path, path.relative_to(source))
        return buffer.getvalue()

    @staticmethod
    def _safe_extract(archive: zipfile.ZipFile, destination: Path) -> None:
        root = destination.resolve()
        for member in archive.infolist():
            target = (root / member.filename).resolve()
            if root not in target.parents and target != root:
                raise ValueError("unsafe archive path")
        archive.extractall(root)


class DriveManager:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def storage_report(self) -> StorageReport:
        usage = shutil.disk_usage(self.root)
        neo_bytes = sum(path.stat().st_size for path in self.root.rglob("*") if path.is_file())
        free_ratio = usage.free / usage.total if usage.total else 0
        status = "critical" if free_ratio < 0.05 else "low" if free_ratio < 0.15 else "healthy"
        return StorageReport(
            str(self.root),
            round(usage.total / 1024**3, 2),
            round(usage.used / 1024**3, 2),
            round(usage.free / 1024**3, 2),
            neo_bytes,
            status,
        )

    def backup_database(self, database: Path, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(".tmp")
        temporary.unlink(missing_ok=True)
        with closing(sqlite3.connect(database)) as source, closing(
            sqlite3.connect(temporary)
        ) as target:
            source.backup(target)
            target.commit()
        os.replace(temporary, destination)
        with closing(sqlite3.connect(destination)) as check:
            result = check.execute("PRAGMA integrity_check").fetchone()[0]
        if result != "ok":
            raise RuntimeError("backup integrity check failed")
        return destination

    def migrate(self, destination: Path) -> MigrationReport:
        destination = destination.expanduser().resolve()
        if destination == self.root or self.root in destination.parents:
            raise ValueError("destination must be outside source")
        destination.mkdir(parents=True, exist_ok=True)
        sources = [
            path
            for path in sorted(self.root.rglob("*"))
            if path.is_file() and not path.is_symlink()
        ]
        required = sum(path.stat().st_size for path in sources)
        if shutil.disk_usage(destination).free < required + 16 * 1024 * 1024:
            raise OSError("destination does not have enough free space")
        manifest: dict[str, dict[str, str | int]] = {}
        bytes_copied = 0
        for source in sources:
            relative = source.relative_to(self.root)
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_suffix(target.suffix + ".neo-copy")
            shutil.copy2(source, temporary)
            os.replace(temporary, target)
            digest = self._sha256(source)
            if self._sha256(target) != digest:
                raise OSError(f"verification failed: {relative}")
            size = source.stat().st_size
            bytes_copied += size
            manifest[str(relative)] = {"sha256": digest, "size": size}
        manifest_path = destination / "NEO-MIGRATION-MANIFEST.json"
        manifest_path.write_text(
            json.dumps(
                {"version": 1, "source": str(self.root), "files": manifest},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return MigrationReport(
            str(self.root), str(destination), len(manifest), bytes_copied, True, str(manifest_path)
        )

    def create_encrypted_export(self, destination: Path, password: str) -> Path:
        with tempfile.TemporaryDirectory(prefix="neo-export-") as temporary:
            staging = Path(temporary)
            for name in ("memory", "profiles", "skills", "projects"):
                source = self.root / name
                if source.exists():
                    shutil.copytree(source, staging / name, symlinks=False)
            metadata = {
                "format": "NEO-MIGRATION",
                "version": 1,
                "created_at": datetime.now(UTC).isoformat(),
            }
            (staging / "manifest.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
            return VaultArchive.encrypt_directory(staging, destination, password)

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
