#!/usr/bin/env bash
set -euo pipefail
neo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -f "$neo_root/NEO_PORTABLE" ]]; then
  echo "NEO portable marker is missing." >&2
  exit 1
fi
export NEO_DATA_DIR="$neo_root/data"
export OLLAMA_MODELS="$neo_root/models"
source_binary="$neo_root/app/linux/NEO"
runtime_root="${XDG_RUNTIME_DIR:-/tmp}/neo-portable-${UID}"
if ! mkdir -p "$runtime_root" 2>/dev/null; then
  runtime_root="/tmp/neo-portable-${UID}"
  mkdir -p "$runtime_root"
fi
fingerprint="$(sha256sum "$source_binary" | cut -d' ' -f1)"
runtime_binary="$runtime_root/NEO-$fingerprint"
if [[ ! -x "$runtime_binary" ]]; then
  cp "$source_binary" "$runtime_binary.tmp"
  chmod 700 "$runtime_binary.tmp"
  mv "$runtime_binary.tmp" "$runtime_binary"
fi
exec "$runtime_binary" "$@"
