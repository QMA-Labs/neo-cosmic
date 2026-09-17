$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

& "$PSScriptRoot\build_windows.ps1"

choco install ollama --no-progress -y
$OllamaCommand = Get-Command ollama -ErrorAction Stop
$Ollama = $OllamaCommand.Source
$env:OLLAMA_MODELS = (Resolve-Path "build").Path + "\ollama-models"
New-Item -ItemType Directory -Force $env:OLLAMA_MODELS | Out-Null
$Server = Start-Process -FilePath $Ollama -ArgumentList "serve" -PassThru -WindowStyle Hidden
try {
    Start-Sleep -Seconds 5
    & $Ollama pull "qwen3.5:0.8b"
    if ($LASTEXITCODE -ne 0) { throw "Ollama model pull failed." }
} finally {
    if ($Server -and -not $Server.HasExited) { Stop-Process -Id $Server.Id -Force }
}

$Candidates = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)
$ISCC = $Candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $ISCC) { throw "Inno Setup 6 (ISCC.exe) was not found." }
& $ISCC "installer\NEO.iss"
if ($LASTEXITCODE -ne 0 -or -not (Test-Path "dist\NEO-Setup.exe")) { throw "Installer compilation failed." }

$Hash = (Get-FileHash "dist\NEO-Setup.exe" -Algorithm SHA256).Hash.ToLower()
Set-Content -Encoding ASCII "dist\NEO-Setup.exe.sha256" "$Hash  NEO-Setup.exe"
Write-Host "Installer ready: dist\NEO-Setup.exe"
