$InstallDir = Join-Path $env:LOCALAPPDATA "NEO\USBWatcher"
$StartupFile = Join-Path ([Environment]::GetFolderPath("Startup")) "NEO USB Watcher.cmd"
Remove-Item $StartupFile -Force -ErrorAction SilentlyContinue
Remove-Item $InstallDir -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "NEO USB watcher removed for this Windows user."
