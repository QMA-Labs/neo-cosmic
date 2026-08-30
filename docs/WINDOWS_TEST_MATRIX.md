# Windows compatibility gate

The final release target is Windows 10/11 x64. Ubuntu is a development host, not the
shipping platform. A release is not complete until the executable passes this matrix.

| Class | Minimum coverage | Expected model |
|---|---|---|
| Office laptop | Intel/AMD integrated GPU, 8 GB RAM | 0.8B / safe mode |
| Mainstream | Integrated GPU, 16 GB RAM | adaptive light model |
| Gaming | NVIDIA RTX 3050/4050, 16 GB RAM | load-dependent |
| Pro | RTX 4060+, 16–32 GB RAM | 9B when VRAM is available |
| Brand coverage | ASUS, Acer, Lenovo, HP, Dell | identical core behavior |

Required checks on every class:

- Windows 10 and Windows 11 startup, first-run consent and clean uninstall.
- 100%, 125%, 150%, 175% and 200% display scaling.
- Single and multiple monitors, taskbar on each edge, sleep/wake and monitor disconnect.
- Drag, click-through policy, always-on-top, minimize/restore and graceful shutdown.
- Ollama running/stopped, both models installed/missing, CPU-only and GPU-busy scenarios.
- Portable data on NTFS removable storage and local-data fallback after removal.
- Non-admin user, Unicode Windows username, Persian/English layout and offline use.
- Idle CPU/memory/GPU budget and no interference with games or creative applications.

Visual quality is a separate release gate: final animation assets, motion system,
expressions, particles, shadows and character customization must replace the current
procedural engineering mascot before declaring the Pet visually final.
