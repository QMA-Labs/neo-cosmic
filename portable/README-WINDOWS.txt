NEO DRIVE — Windows 10/11 x64

1. Keep this folder on an NTFS/exFAT USB drive.
2. Install Ollama on the host laptop (GPU drivers/runtime remain host responsibilities).
3. Run START_OLLAMA_PORTABLE.cmd so Ollama uses this drive's models folder.
4. In another terminal, pull qwen3.5:0.8b and qwen3.5:9b once for this drive.
5. Double-click START_NEO.cmd.
6. Review and approve permissions separately for every new machine.

NEO never needs a fixed drive letter. Brain, profiles, backups and learned information stay
under data/ on this drive. Removing the drive while NEO is writing can corrupt data: close
NEO first and use Windows "Safely Remove Hardware".

This Windows build cannot run on Android, iOS, macOS or Linux. Those platforms require
separate native builds. GPU support also depends on the host drivers and Ollama.
