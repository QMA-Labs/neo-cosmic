$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    $Uv = Get-Command uv -ErrorAction SilentlyContinue
    if ($Uv) { uv venv --python 3.13 .venv } else { python -m venv .venv }
}

& .venv\Scripts\python.exe -m pip install -e ".[dev]" pyinstaller
& .venv\Scripts\python.exe -m pytest
& .venv\Scripts\ruff.exe check .
& .venv\Scripts\pyinstaller.exe --clean --noconfirm neo.spec

$Release = "dist\NEO-DRIVE"
if (Test-Path $Release) { Remove-Item $Release -Recurse -Force }
New-Item -ItemType Directory -Force "$Release\app", "$Release\data", "$Release\models", "$Release\backups" | Out-Null
Copy-Item "dist\NEO.exe" "$Release\app\NEO.exe" -Force
New-Item -ItemType File -Force "$Release\NEO_PORTABLE" | Out-Null
Copy-Item ".env.example" "$Release\.env.example" -Force
Copy-Item "portable\START_NEO.cmd" "$Release\START_NEO.cmd" -Force
Copy-Item "portable\START_OLLAMA_PORTABLE.cmd" "$Release\START_OLLAMA_PORTABLE.cmd" -Force
Copy-Item "portable\README-WINDOWS.txt" "$Release\README-WINDOWS.txt" -Force
Copy-Item "portable\INSTALL_WINDOWS_AUTOSTART.ps1" "$Release\INSTALL_WINDOWS_AUTOSTART.ps1" -Force
Copy-Item "portable\UNINSTALL_WINDOWS_AUTOSTART.ps1" "$Release\UNINSTALL_WINDOWS_AUTOSTART.ps1" -Force
Copy-Item "portable\windows-usb-watcher.ps1" "$Release\windows-usb-watcher.ps1" -Force
Set-Content -Encoding UTF8 "$Release\models\PUT_OLLAMA_MODELS_HERE.txt" "Models remain managed by Ollama. NEO sets OLLAMA_MODELS to this folder when launched from this drive."

Compress-Archive -Path "$Release\*" -DestinationPath "dist\NEO-DRIVE-WINDOWS-X64.zip" -Force
$Hash = (Get-FileHash "dist\NEO-DRIVE-WINDOWS-X64.zip" -Algorithm SHA256).Hash.ToLower()
Set-Content -Encoding ASCII "dist\NEO-DRIVE-WINDOWS-X64.zip.sha256" "$Hash  NEO-DRIVE-WINDOWS-X64.zip"
Write-Host "Portable drive ready: dist\NEO-DRIVE-WINDOWS-X64.zip"
