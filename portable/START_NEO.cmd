@echo off
setlocal
cd /d "%~dp0"
if not exist "NEO_PORTABLE" (
  echo NEO portable marker is missing.
  pause
  exit /b 1
)
if not exist "app\NEO.exe" (
  echo app\NEO.exe is missing or was quarantined.
  pause
  exit /b 1
)
set "NEO_DATA_DIR=%~dp0data"
set "OLLAMA_MODELS=%~dp0models"
start "NEO" "%~dp0app\NEO.exe"
endlocal
