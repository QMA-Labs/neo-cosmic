#define MyAppName "NEO Cosmic"
#define MyAppVersion "1.2.0"
#define MyAppPublisher "QMA Labs"
#define MyAppExeName "NEO.exe"

[Setup]
AppId={{5E9E7149-E1A4-46F4-9C5B-7BEA23756D9D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=NEO Cosmic Windows Installer
DefaultDirName={autopf}\NEO Cosmic
DefaultGroupName=NEO Cosmic
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist
OutputBaseFilename=NEO-Setup
SetupIconFile=..\build\neo.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\NEO.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\portable\README-WINDOWS.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\.env.example"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\build\ollama-models\*"; DestDir: "{userprofile}\.ollama\models"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\NEO Cosmic"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\NEO Cosmic"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -Command ""if (-not (Test-Path $env:LOCALAPPDATA\Programs\Ollama\ollama.exe)) {{ irm https://ollama.com/install.ps1 | iex }}"""; StatusMsg: "Installing Ollama..."; Flags: waituntilterminated
Filename: "{app}\{#MyAppExeName}"; Description: "Launch NEO Cosmic"; Flags: nowait postinstall skipifsilent

[Code]
function OllamaInstalled: Boolean;
begin
  Result := FileExists(ExpandConstant('{localappdata}\Programs\Ollama\ollama.exe')) or
            FileExists(ExpandConstant('{userappdata}\Ollama\ollama.exe')) or
            FileExists(ExpandConstant('{pf}\Ollama\ollama.exe'));
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep = ssPostInstall) and (not OllamaInstalled) and (not WizardSilent) then
    MsgBox('Ollama installation did not complete. Run NEO Setup again while connected to the internet.', mbError, MB_OK);
end;
