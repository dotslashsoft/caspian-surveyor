#define MyAppName "Caspian Surveyor"
#define MyAppVersion "0.9.0.0"
#define MyAppExeName "CaspianSurveyor.exe"

[Setup]
AppId={{5B42D98A-4C6A-4C6F-A8E8-2CC2BBF32B79}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={localappdata}\Programs\CaspianSurveyor
DefaultGroupName={#MyAppName}
PrivilegesRequired=lowest
SetupArchitecture=x64
Compression=lzma2
SolidCompression=yes
OutputDir=installer
OutputBaseFilename=CaspianSurveyor-{#MyAppVersion}-Setup
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\CaspianSurveyor.ico
SetupIconFile=CaspianSurveyor.ico
LicenseFile=LICENSE

[Files]
Source: "dist\CaspianSurveyor\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "CaspianSurveyor.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "licenses\*"; DestDir: "{app}\licenses"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\CaspianSurveyor.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\CaspianSurveyor.ico"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent