@echo off
setlocal
cd /d "%~dp0"
where ollama.exe >nul 2>&1
if errorlevel 1 (
  echo Ollama is not installed on this Windows laptop.
  echo Install Ollama, then run this file again.
  pause
  exit /b 1
)
curl.exe --silent --fail http://127.0.0.1:11434/api/tags >nul 2>&1
if not errorlevel 1 (
  echo Another Ollama service is already running.
  echo Stop it first if you want models to be loaded from this NEO drive.
  pause
  exit /b 2
)
set "OLLAMA_MODELS=%~dp0models"
echo Starting Ollama with models stored on: %OLLAMA_MODELS%
ollama.exe serve
endlocal
