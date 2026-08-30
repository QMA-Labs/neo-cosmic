#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"

.venv/bin/python -m pytest
.venv/bin/ruff check .
.venv/bin/pyinstaller --clean --noconfirm neo.spec

release="dist/NEO-DRIVE-LINUX-X64"
rm -rf "$release"
mkdir -p "$release/app/linux" "$release/data" "$release/models" "$release/backups"
cp "dist/NEO" "$release/app/linux/NEO"
chmod +x "$release/app/linux/NEO"
touch "$release/NEO_PORTABLE"
cp "portable/START_NEO_LINUX.sh" "$release/START_NEO_LINUX.sh"
cp "portable/START_OLLAMA_PORTABLE_LINUX.sh" "$release/START_OLLAMA_PORTABLE_LINUX.sh"
cp "portable/INSTALL_LINUX_AUTOSTART.sh" "$release/INSTALL_LINUX_AUTOSTART.sh"
cp "portable/UNINSTALL_LINUX_AUTOSTART.sh" "$release/UNINSTALL_LINUX_AUTOSTART.sh"
cp "portable/linux-usb-watcher.sh" "$release/linux-usb-watcher.sh"
cp "portable/README-LINUX.txt" "$release/README-LINUX.txt"
chmod +x "$release"/*.sh
tar -C "$release" -czf "dist/NEO-DRIVE-LINUX-X64.tar.gz" .
sha256sum "dist/NEO-DRIVE-LINUX-X64.tar.gz" > "dist/NEO-DRIVE-LINUX-X64.tar.gz.sha256"
echo "Linux portable drive ready: dist/NEO-DRIVE-LINUX-X64.tar.gz"
