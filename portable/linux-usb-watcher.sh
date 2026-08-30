#!/usr/bin/env bash
set -euo pipefail

lock_file="${XDG_RUNTIME_DIR:-/tmp}/neo-usb-watcher-${UID}.lock"
exec 9>"$lock_file"
flock -n 9 || exit 0

declare -A launched=()
while true; do
  for base in "/media/$USER" "/run/media/$USER"; do
    [[ -d "$base" ]] || continue
    while IFS= read -r -d '' marker; do
      root="${marker%/NEO_PORTABLE}"
      launcher="$root/START_NEO_LINUX.sh"
      [[ -x "$launcher" ]] || continue
      if [[ -z "${launched[$root]:-}" ]]; then
        "$launcher" >/dev/null 2>&1 &
        launched[$root]=1
      fi
    done < <(find "$base" -mindepth 2 -maxdepth 2 -type f -name NEO_PORTABLE -print0 2>/dev/null)
  done
  for root in "${!launched[@]}"; do
    [[ -f "$root/NEO_PORTABLE" ]] || unset 'launched[$root]'
  done
  sleep 5
done
