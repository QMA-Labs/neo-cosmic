$ErrorActionPreference = "Stop"
$InstallDir = Join-Path $env:LOCALAPPDATA "NEO\USBWatcher"
$StartupDir = [Environment]::GetFolderPath("Startup")
New-Item -ItemType Directory -Force $InstallDir | Out-Null
Copy-Item (Join-Path $PSScriptRoot "windows-usb-watcher.ps1") (Join-Path $InstallDir "watcher.ps1") -Force
$ShortcutPath = Join-Path $StartupDir "NEO USB Watcher.cmd"
$Command = '@echo off' + "`r`n" + 'powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "' + (Join-Path $InstallDir "watcher.ps1") + '"'
Set-Content -Path $ShortcutPath -Value $Command -Encoding ASCII
Write-Host "NEO USB watcher installed for this Windows user. It starts at next sign-in."
