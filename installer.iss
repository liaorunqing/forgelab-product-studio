#define AppName "ForgeLab AI Product Studio"
#define AppVersion "1.0.0"
#define AppPublisher "ForgeLab"
#define AppExeName "ForgeLabServer.exe"

[Setup]
AppId={{B5E6BDB6-2A0A-4A0C-8A0F-5DF5D1F6E1F2}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\ForgeLab
DefaultGroupName={#AppName}
OutputDir=dist\installer
OutputBaseFilename=ForgeLab-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Files]
Source: "dist\ForgeLab\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\ForgeLab AI Product Studio"; Filename: "{app}\{#AppExeName}"
Name: "{commondesktop}\ForgeLab AI Product Studio"; Filename: "{app}\{#AppExeName}"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "启动 ForgeLab"; Flags: nowait postinstall skipifsilent
