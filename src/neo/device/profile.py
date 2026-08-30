from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import socket
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import psutil

from neo.core.hardware import HardwareInfo, detect_hardware


def _read(path: str) -> str | None:
    try:
        value = Path(path).read_text(encoding="utf-8", errors="replace").strip()
        return value or None
    except OSError:
        return None


def _command(args: list[str]) -> str | None:
    if not shutil.which(args[0]):
        return None
    try:
        output = subprocess.run(
            args, check=True, capture_output=True, text=True, timeout=3
        ).stdout.strip()
        return output or None
    except (OSError, subprocess.SubprocessError):
        return None


@dataclass(frozen=True, slots=True)
class DiskProfile:
    device: str
    mountpoint: str
    filesystem: str
    total_gb: float
    free_gb: float
    removable: bool


@dataclass(frozen=True, slots=True)
class MachineProfile:
    profile_version: int
    machine_id: str
    hostname: str
    manufacturer: str | None
    model: str | None
    serial_hash: str | None
    operating_system: str
    kernel: str
    architecture: str
    cpu_model: str
    hardware: HardwareInfo
    disks: tuple[DiskProfile, ...]
    connected_usb: tuple[str, ...]
    captured_at: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class DeviceProfiler:
    """Builds privacy-conscious machine profiles on Windows and Linux."""

    def capture(self) -> MachineProfile:
        machine_seed = self._machine_seed()
        serial = self._system_value("serial")
        cpu_model = self._cpu_model()
        return MachineProfile(
            profile_version=1,
            machine_id=hashlib.sha256(machine_seed.encode()).hexdigest()[:20],
            hostname=socket.gethostname(),
            manufacturer=self._system_value("manufacturer"),
            model=self._system_value("model"),
            serial_hash=(hashlib.sha256(serial.encode()).hexdigest()[:16] if serial else None),
            operating_system=self._os_name(),
            kernel=platform.release(),
            architecture=platform.machine(),
            cpu_model=cpu_model,
            hardware=detect_hardware(),
            disks=self._disks(),
            connected_usb=self._usb_devices(),
            captured_at=datetime.now(UTC).isoformat(),
        )

    def save(self, profile: MachineProfile, directory: Path) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / f"{profile.machine_id}.json"
        temporary = target.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(profile.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        os.replace(temporary, target)
        return target

    @staticmethod
    def _os_name() -> str:
        if platform.system() == "Linux":
            info = platform.freedesktop_os_release()
            return info.get("PRETTY_NAME", platform.platform())
        return platform.platform()

    @staticmethod
    def _machine_seed() -> str:
        if platform.system() == "Windows":
            value = _command(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    "(Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Cryptography').MachineGuid",
                ]
            )
            return value or socket.gethostname()
        return _read("/etc/machine-id") or socket.gethostname()

    @staticmethod
    def _system_value(name: str) -> str | None:
        linux_paths = {
            "manufacturer": "/sys/class/dmi/id/sys_vendor",
            "model": "/sys/class/dmi/id/product_name",
            "serial": "/sys/class/dmi/id/product_serial",
        }
        if platform.system() != "Windows":
            return _read(linux_paths[name])
        properties = {
            "manufacturer": "Manufacturer",
            "model": "Model",
            "serial": "IdentifyingNumber",
        }
        class_name = "Win32_ComputerSystemProduct" if name == "serial" else "Win32_ComputerSystem"
        command = (
            f"(Get-CimInstance {class_name} | Select-Object -First 1 "
            f"-ExpandProperty {properties[name]})"
        )
        return _command(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command])

    @staticmethod
    def _cpu_model() -> str:
        if platform.system() == "Windows":
            return (
                _command(
                    [
                        "powershell.exe",
                        "-NoProfile",
                        "-NonInteractive",
                        "-Command",
                        "(Get-CimInstance Win32_Processor | Select-Object -First 1 -Expand Name)",
                    ]
                )
                or platform.processor()
                or "Unknown CPU"
            )
        for line in (_read("/proc/cpuinfo") or "").splitlines():
            if line.lower().startswith("model name") and ":" in line:
                return line.split(":", 1)[1].strip()
        return platform.processor() or "Unknown CPU"

    @staticmethod
    def _disks() -> tuple[DiskProfile, ...]:
        disks = []
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
            except OSError:
                continue
            mount = Path(part.mountpoint)
            removable = DeviceProfiler._is_removable_mount(mount)
            disks.append(
                DiskProfile(
                    device=part.device,
                    mountpoint=part.mountpoint,
                    filesystem=part.fstype,
                    total_gb=round(usage.total / 1024**3, 2),
                    free_gb=round(usage.free / 1024**3, 2),
                    removable=removable,
                )
            )
        return tuple(disks)

    @staticmethod
    def _is_removable_mount(mount: Path) -> bool:
        if platform.system() == "Windows":
            try:
                import ctypes

                return ctypes.windll.kernel32.GetDriveTypeW(str(mount)) == 2
            except (AttributeError, OSError):
                return False
        return str(mount).startswith(("/media/", "/run/media/"))

    @staticmethod
    def _usb_devices() -> tuple[str, ...]:
        if platform.system() == "Windows":
            output = _command(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    "Get-PnpDevice -PresentOnly | Where-Object InstanceId -like 'USB*' | "
                    "Select-Object -ExpandProperty FriendlyName",
                ]
            )
            return tuple(line.strip() for line in (output or "").splitlines() if line.strip())
        output = _command(["lsusb"])
        if not output:
            return ()
        devices = []
        for line in output.splitlines():
            description = line.split(" ID ", 1)[-1]
            devices.append(description.split(" ", 1)[-1] if " " in description else description)
        return tuple(devices)
