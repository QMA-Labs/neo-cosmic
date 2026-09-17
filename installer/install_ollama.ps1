$ErrorActionPreference = "Stop"
$paths = @(
  "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe",
  "$env:APPDATA\Ollama\ollama.exe",
  "$env:ProgramFiles\Ollama\ollama.exe"
)
if ($paths | Where-Object { Test-Path $_ }) { exit 0 }
$installer = Join-Path $env:TEMP "OllamaSetup.exe"
Invoke-WebRequest "https://ollama.com/download/OllamaSetup.exe" -OutFile $installer
Start-Process -FilePath $installer -ArgumentList "/VERYSILENT /NORESTART" -Wait
if (-not ($paths | Where-Object { Test-Path $_ })) { throw "Ollama installation did not complete." }
