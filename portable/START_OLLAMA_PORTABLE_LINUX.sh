#!/usr/bin/env bash
set -euo pipefail
neo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if ! command -v ollama >/dev/null 2>&1; then
  echo "Ollama is not installed on this Linux laptop." >&2
  exit 1
fi
if curl --silent --fail http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  echo "Another Ollama service is already running. Stop it first to use USB models." >&2
  exit 2
fi
export OLLAMA_MODELS="$neo_root/models"
echo "Starting Ollama with models stored in $OLLAMA_MODELS"
exec ollama serve
