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


$Iss = @'
#define AppName "NEO Cosmic"
#define AppVersion "1.2.0"
[Setup]
AppId={{5E9E7149-E1A4-46F4-9C5B-7BEA23756D9D}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=QMA Labs
VersionInfoVersion={#AppVersion}
VersionInfoCompany=QMA Labs
VersionInfoDescription=NEO Cosmic Windows Installer
DefaultDirName={autopf}\NEO Cosmic
DefaultGroupName=NEO Cosmic
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=dist
OutputBaseFilename=NEO-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\NEO.exe
[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked
[Files]
Source: "dist\NEO.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "portable\README-WINDOWS.txt"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{autoprograms}\NEO Cosmic"; Filename: "{app}\NEO.exe"
Name: "{autodesktop}\NEO Cosmic"; Filename: "{app}\NEO.exe"; Tasks: desktopicon
[Run]
Filename: "{app}\NEO.exe"; Description: "Launch NEO Cosmic"; Flags: nowait postinstall skipifsilent
[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    if not FileExists(ExpandConstant('{localappdata}\Programs\Ollama\ollama.exe')) then
      MsgBox('Ollama was not detected. Install it from ollama.com, then download qwen3.5:0.8b or qwen3.5:9b. Models are intentionally not bundled.', mbInformation, MB_OK);
end;
'@
Set-Content -Path "NEO.iss" -Value $Iss -Encoding UTF8
$ISCC = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $ISCC)) { $ISCC = "C:\Program Files\Inno Setup 6\ISCC.exe" }
& $ISCC "NEO.iss"
if (-not (Test-Path "dist\NEO-Setup.exe")) { throw "Installer was not created." }
$SetupHash = (Get-FileHash "dist\NEO-Setup.exe" -Algorithm SHA256).Hash.ToLower()
Set-Content -Encoding ASCII "dist\NEO-Setup.exe.sha256" "$SetupHash  NEO-Setup.exe"
Write-Host "Windows installer ready."
