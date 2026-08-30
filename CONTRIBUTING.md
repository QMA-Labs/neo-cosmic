# Contributing to NEO

Keep changes local-first, permission-gated and cross-platform. Never add telemetry or upload
local memory, file contents, screenshots or machine profiles without a separate explicit
opt-in design and tests.

Before opening a pull request:

```bash
python -m ruff check .
python -m pytest
python scripts/smoke_test.py
```

Changes to system actions must use typed operations, show an exact preview, request a fresh
confirmation and include a failure/undo test. UI work must preserve Persian RTL and English
LTR behavior. Never expose model chain-of-thought or raw internal prompts.
