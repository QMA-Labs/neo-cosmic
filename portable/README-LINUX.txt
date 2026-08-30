NEO DRIVE — Linux x86_64

Manual mode (no host installation):
1. Install/start Ollama on the Linux laptop.
2. Run START_OLLAMA_PORTABLE_LINUX.sh in one terminal if models should stay on USB.
3. Run START_NEO_LINUX.sh.
4. Approve permissions separately for this machine.

Optional automatic Pet:
Run INSTALL_LINUX_AUTOSTART.sh once on each trusted Linux laptop. This installs a small
per-user watcher under ~/.local/share and a desktop autostart entry. It launches only a
mounted drive containing both NEO_PORTABLE and an executable START_NEO_LINUX.sh. Remove it
at any time with UNINSTALL_LINUX_AUTOSTART.sh.

The Windows and Linux executables may share data/, models/ and backups/ on the same drive.
Use exFAT for easiest cross-platform write support, or NTFS only when Linux NTFS support is
known to be reliable. Always close NEO before safely ejecting the drive.

If the USB filesystem is mounted noexec, the launcher caches only the signed/fingerprinted
Linux executable in the per-user runtime directory. Data, models and the Brain remain on
USB; the runtime cache is not an installation and normally disappears after reboot.
