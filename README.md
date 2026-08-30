<div align="center">
  <img src="src/neo/app/assets/neo-cosmic-v1.png" width="260" alt="NEO Cosmic character">
  <h1>NEO Cosmic 1.2</h1>
  <p><strong>A private, local-first AI companion that lives on your desktop.</strong></p>
  <p>Persian RTL · English LTR · Ollama · Adaptive models · Portable Brain</p>
</div>

---

> Final portable release for Ubuntu/Linux x86_64 and Windows 10/11 x64. Build each executable on its own operating system; both can share the same Brain data on one USB.

NEO is a local-first cosmic desktop companion with Persian RTL chat, cancelable answers, a private persistent Brain, permission-gated file/screen discovery, hardware telemetry, explicit web search and a control center. It detects host resources, chooses between `qwen3.5:9b` and `qwen3.5:0.8b`, talks to Ollama, persists memory in SQLite, and creates privacy-conscious machine profiles.

## Why NEO is different

| Capability | What it means |
| --- | --- |
| Local-first intelligence | Conversations run through your own Ollama models. |
| Portable Brain | Memory can stay on a USB drive and move between trusted computers. |
| Adaptive routing | NEO selects 9B or 0.8B from real RAM, VRAM and system load. |
| Explicit permissions | Files, screen, web and device discovery are approved separately. |
| Bilingual interface | First-run Persian/English choice with RTL/LTR conversation support. |
| Specialist chats | Companion, Expert, Coder, Philosophy and Web Research personalities. |
| Live awareness | CPU, RAM, GPU, VRAM, storage, battery and network telemetry. |
| Resilient desktop UI | Background work, cancelable answers and graceful offline behavior. |

> NEO does not silently read files, capture the screen, access accounts or modify the host. Capability is not consent: every sensitive integration remains separately permission-gated.

## Specialist conversations

The in-panel selector switches between Companion, Expert, Coder, Philosophy and Web Research modes. The selected mode persists locally. Web Research remains separately permission-gated. NEO follows the language of each question and never displays model chain-of-thought.

## Install

Python 3.11+ and Ollama are expected.

```bash
cd ~/projects/NEO
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp .env.example .env
```

## Run

```bash
neo status
neo device
neo-pet
```

Ollama being offline never prevents startup. For chat, start Ollama and ensure the configured models exist:

```bash
ollama list
ollama serve
```

## Quality checks

```bash
ruff check .
black --check .
pytest
python scripts/smoke_test.py
```

## Portable builds

Linux:

```bash
bash scripts/build_linux.sh
```

Windows PowerShell:

```powershell
.\scripts\build_windows.ps1
```

The Windows result is `dist\NEO-DRIVE-WINDOWS-X64.zip`. PyInstaller must build each native executable on its target operating system; GitHub Actions includes the Windows-native build.

## Privacy model

Discovery never runs without explicit consent. Screen capture is on-demand, rate-limited and disabled until explicit consent. Images are sent only to the configured local Ollama endpoint and are not persisted by default. System actions are typed and permission-gated; arbitrary shell strings are not accepted.

Memory is stored at `<data-dir>/memory/neo.sqlite3` with SQLite WAL. Logs are at `<data-dir>/logs/neo.log`. The router uses current CPU/RAM load, available RAM and NVIDIA VRAM when available.

See [SECURITY.md](SECURITY.md) and [CONTRIBUTING.md](CONTRIBUTING.md) before contributing.