$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

& "$PSScriptRoot\build_windows.ps1"
& "$PSScriptRoot\fetch_ollama_model.ps1" -Model "qwen3.5" -Tag "0.8b"

$Candidates = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)
$ISCC = $Candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $ISCC) { throw "Inno Setup 6 (ISCC.exe) was not found." }

& $ISCC "installer\NEO.iss"
if (-not (Test-Path "dist\NEO-Setup.exe")) { throw "Installer output was not created." }

$Hash = (Get-FileHash "dist\NEO-Setup.exe" -Algorithm SHA256).Hash.ToLower()
Set-Content -Encoding ASCII "dist\NEO-Setup.exe.sha256" "$Hash  NEO-Setup.exe"
Write-Host "Installer ready: dist\NEO-Setup.exe"
