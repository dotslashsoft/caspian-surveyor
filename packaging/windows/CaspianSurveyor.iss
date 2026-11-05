#define MyAppName "Caspian Surveyor"
#define MyAppVersion "0.9.9.0"
#define MyAppExeName "CaspianSurveyor.exe"

[Setup]
AppId={{5B42D98A-4C6A-4C6F-A8E8-2CC2BBF32B79}
AppName={#MyAppName}
AppVersion={#MyAppVersion}

SourceDir=..\..

DefaultDirName={localappdata}\Programs\CaspianSurveyor
DefaultGroupName={#MyAppName}
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
Compression=lzma2
SolidCompression=yes

OutputDir=installer
OutputBaseFilename=CaspianSurveyor-{#MyAppVersion}-Setup

UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\CaspianSurveyor.ico

SetupIconFile=packaging\windows\CaspianSurveyor.ico
LicenseFile=LICENSE

[Files]
Source: "dist\CaspianSurveyor\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "packaging\windows\CaspianSurveyor.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "licenses\*"; DestDir: "{app}\licenses"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "src\caspian_surveyor\assets\historical_event_ingestion.ini"; DestDir: "{localappdata}\CaspianSurveyor\data"; Flags: ignoreversion uninsneveruninstall; Check: Needs0990Migration
Source: "src\caspian_surveyor\assets\overlay_config.json"; DestDir: "{localappdata}\CaspianSurveyor\config"; Flags: onlyifdoesntexist uninsneveruninstall

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\CaspianSurveyor.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\CaspianSurveyor.ico"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Code]
function MigrationMarkerPath(): String;
begin
  Result := ExpandConstant('{localappdata}\CaspianSurveyor\data\migration_0990.done');
end;

function Needs0990Migration(): Boolean;
begin
  Result := not FileExists(MigrationMarkerPath());
end;

procedure reset_caspian_database_state();
var
  db_file_path   : String;
  db_backup_path : String;
  jsonl_file_path   : String;
  jsonl_backup_path : String;
begin
  if not Needs0990Migration() then
  begin
    Log('0.9.9.0 migration already completed. Skipping.');
    Exit;
  end;

  db_file_path := ExpandConstant('{localappdata}\CaspianSurveyor\data\db\caspian_surveyor.db');
  db_backup_path := ExpandConstant('{localappdata}\CaspianSurveyor\data\db\caspian_surveyor_PRE-0990.bak');
  jsonl_file_path := ExpandConstant('{localappdata}\CaspianSurveyor\data\exploration_history.jsonl');
  jsonl_backup_path := ExpandConstant('{localappdata}\CaspianSurveyor\data\exploration_history_PRE-0990.jsonl');

  if FileExists(db_file_path) then
  begin
    if not FileExists(db_backup_path) then
    begin
      if RenameFile(db_file_path, db_backup_path) then
        Log('Success: Original database preserved as .bak')
      else
        RaiseException('Failed to rename existing Caspian database.');
    end
    else
      Log('Pre-0.9.9.0 database backup exists. Skipping rename.');
  end
  else
    Log('No existing database found. Skipping rename.');

  // Preserve existing JSONL archive before historical reingestion.
  if FileExists(jsonl_file_path) then
  begin
    if not FileExists(jsonl_backup_path) then
    begin
      if RenameFile(jsonl_file_path, jsonl_backup_path) then
        Log('Success: Historical JSONL archive preserved.')
      else
        RaiseException('Failed to rename historical JSONL archive.');
    end
    else
      Log('Pre-0.9.9.0 JSONL backup exists. Skipping rename.');
  end;

  // Record that the 0.9.9.0 setup migration has run.
  if not SaveStringToFile(MigrationMarkerPath(), '0.9.9.0', False) then
    RaiseException('Failed to record migration completion.');
end;

// Inno Setup hook
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    reset_caspian_database_state();
end;