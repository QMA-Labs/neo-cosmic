<div align="center">
  <img src="src/neo/app/assets/neo-cosmic-v1.png" width="260" alt="NEO Cosmic character">
  <h1>NEO Cosmic 1.2</h1>
  <p><strong>A private, local-first AI companion that lives on your desktop.</strong></p>
  <p>Persian RTL · English LTR · Ollama · Adaptive models · Portable Brain</p>
</div>

---

> Final portable release for Ubuntu/Linux x86_64 and Windows 10/11 x64. Build each
> executable on its own operating system; both can share the same Brain data on one USB.

NEO is a local-first cosmic desktop companion with Persian RTL chat, cancelable answers,
a private persistent Brain, permission-gated file/screen discovery, hardware telemetry,
explicit web search and a control center. It detects host resources,
chooses between `qwen3.5:9b` and `qwen3.5:0.8b`, discovers an optional removable data
location, talks to Ollama, persists memory in SQLite, and creates privacy-conscious machine
profiles. The transparent PySide6 Pet provides chat, drag/click interaction and visible
idle/thinking/loading/success states.

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

> NEO does not silently read files, capture the screen, access accounts or modify the host.
> Capability is not consent: every sensitive integration remains separately permission-gated.

## Specialist conversations

The in-panel selector switches between Companion, Expert, Coder, Philosophy and Web
Research modes. The selected mode persists locally. Web Research remains separately
permission-gated; switching mode never grants network access by itself. NEO follows the
language of each question and never displays model chain-of-thought.

## Install

Python 3.11+ and Ollama are expected to be installed already.

```bash
cd ~/projects/NEO
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp .env.example .env
```

An empty `NEO_DATA_DIR` uses `${XDG_DATA_HOME:-~/.local/share}/neo`. Set it in `.env`
to keep NEO data elsewhere. Set `NEO_PREFER_REMOVABLE=true` to use the first writable
mount under `/media` or `/run/media`; NEO safely falls back to the configured local path.

## Run

```bash
neo status
neo device
neo-pet
neo memory set owner '{"name":"Masiha"}'
neo memory get owner
neo memory list
python -m neo status
```

Ollama being offline never prevents startup or status checks. To use the selected model,
start Ollama and ensure the configured models exist:

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

## Final portable builds

Ubuntu/Linux:

```bash
bash scripts/build_linux.sh
```

Windows — run natively in PowerShell on Windows:

Run from PowerShell on Windows:

```powershell
.\scripts\build_windows.ps1
```

The result is `dist\NEO-DRIVE-WINDOWS-X64.zip`. Release acceptance follows
`docs/WINDOWS_TEST_MATRIX.md`. PyInstaller cannot produce a trustworthy Windows `.exe`
from Linux; the included GitHub Actions workflow runs the same native Windows build.

## Adaptive AI and Memory Brain

The router refreshes hardware load and selects Eco, Light, Compatibility or Pro execution.
High-complexity work can temporarily promote a CPU-only machine to the 9B model, while a
busy GPU safely falls back to the light model. Context size, GPU offload and keep-alive are
sent to Ollama per decision.

Memory supports `core`, `learned` and expiring `temporary` records, confidence, source,
evidence, protected Never Forget entries, audited edits/deletes, search and graph relations.

```bash
neo memory set person.mom.color purple --kind core --protect --source user --confidence .95
neo memory search purple
neo memory set session.note temporary --kind temporary --ttl 3600
neo memory relate person.mom likes color.purple --confidence .95
neo memory delete person.mom.color --force
```

## Silent discovery, people and projects

Discovery never runs without explicit consent. Use `--metadata-only` when content must not
be read. Generated people and project knowledge remains in the same portable Memory Brain.

```bash
neo discover ~/Documents ~/projects --grant --metadata-only
neo people add Sara --alias مامان --alias Mom
neo people import-vcard contacts.vcf
neo people propose-owner
neo projects ~/projects --max-depth 6
```

System-derived owner names are low-confidence proposals, never confirmed identities.
Project commands generated by detection remain untrusted until the user approves execution.

## Screen intelligence and typed Windows agent

Screen capture is on-demand, rate-limited and disabled until explicit consent. Images are
sent only to the configured local Ollama endpoint and are not persisted by default.

```bash
neo screen grant
neo screen app
neo screen analyze "مشکل روی صفحه چیست؟"
neo screen revoke
```

System actions are typed and permission-gated; arbitrary shell strings are not accepted.
Always inspect the preview before granting an action in product UI.

```bash
neo agent grant write_file once
neo agent run write_file --target ./note.txt --arguments '{"content":"hello"}'
neo agent grant git_status project --target ~/projects/NEO
neo agent run git_status --target ~/projects/NEO
```

File writes, moves and copies are verified and have a seven-day undo record. Fixed,
read-only adapters cover Git status, Docker containers, Ollama models, Windows service
status and Task Scheduler listing. Windows mutations remain disabled until a dedicated,
individually verified typed action is implemented.

## Learning, evolution and portable drive

Learning records corrections, failures and successful workflows with evidence. Evolved
skills remain proposals until the user approves them; NEO never rewrites its own code.

```bash
neo learn correct preferred.color blue purple
neo learn failure build "exit code 1" --action pytest
neo learn consolidate
```

Drive operations preserve the source, use verified SQLite backups and produce encrypted
`.neo` exports. Archive passwords are requested interactively and never passed as command
arguments. Use a unique password of at least 12 characters and keep it outside the drive.

```bash
neo drive status
neo drive backup /safe/location/neo-backup.sqlite3
neo drive export /safe/location/NEO-MIGRATION.neo
neo drive import /safe/location/NEO-MIGRATION.neo /new/NEO
neo drive migrate /media/user/NEW-NEO
```

Archives use AES-256-GCM with scrypt, random salt and nonce. Migration checks capacity,
copies atomically, verifies every SHA-256 checksum, writes a manifest and never deletes
the source drive.

Memory is stored at `<data-dir>/memory/neo.sqlite3` with SQLite WAL enabled. Logs are at
`<data-dir>/logs/neo.log`. The router uses current CPU/RAM load, available RAM, NVIDIA
VRAM (when `nvidia-smi` is available), and conservative thresholds configurable in `.env`.
