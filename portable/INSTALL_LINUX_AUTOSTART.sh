#!/usr/bin/env bash
set -euo pipefail

install_dir="$HOME/.local/share/neo-usb-watcher"
autostart_dir="$HOME/.config/autostart"
mkdir -p "$install_dir" "$autostart_dir"

cp "$(dirname "${BASH_SOURCE[0]}")/linux-usb-watcher.sh" "$install_dir/watcher.sh"
chmod +x "$install_dir/watcher.sh"
cat > "$autostart_dir/neo-usb-watcher.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=NEO USB Watcher
Comment=Launch NEO only when a drive containing NEO_PORTABLE is mounted
Exec=$install_dir/watcher.sh
Terminal=false
X-GNOME-Autostart-enabled=true
EOF

echo "NEO USB watcher installed for this Linux user. Log out/in or run:"
echo "$install_dir/watcher.sh"
