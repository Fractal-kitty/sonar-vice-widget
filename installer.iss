; ============================================================
; Sonar Vice Widget - Inno Setup Installer Script
; Compile with Inno Setup 6: https://jrsoftware.org/isdl.php
;
; Oncelikle build.bat ile EXE olusturun,
; ardindan bu dosyayi Inno Setup ile derleyin.
; ============================================================

#define MyAppName "Sonar Vice Widget"
#define MyAppVersion "3.0"
#define MyAppPublisher "Kingpindev"
#define MyAppURL "https://github.com/kingpindev"
#define MyAppExeName "SonarViceWidget.exe"

[Setup]
AppId={{B7E2A9F1-4C3D-4E5F-8A6B-1234567890AB}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=SonarViceWidget_Setup
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardSizePercent=120
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
AllowNoIcons=yes
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Masaustune kisayol olustur"; GroupDescription: "Ek gorevler:"; Flags: unchecked
Name: "startupentry"; Description: "Windows ile otomatik baslat"; GroupDescription: "Ek gorevler:"

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"
Name: "{group}\{#MyAppName} Kaldir"; Filename: "{uninstallexe}"; IconFilename: "{app}\icon.ico"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon
Name: "{commonstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startupentry

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Sonar Vice Widget'i simdi baslat"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "taskkill"; Parameters: "/F /IM {#MyAppExeName}"; Flags: runhidden; RunOnceId: "KillApp"

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
Type: files; Name: "{localappdata}\SonarViceWidget\widget_settings.json"
Type: dirifempty; Name: "{localappdata}\SonarViceWidget"

[Code]
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  Exec('taskkill', '/F /IM SonarViceWidget.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

function InitializeUninstall(): Boolean;
begin
  Result := MsgBox('{#MyAppName} uygulamasini kaldirmak istediginizden emin misiniz?',
                   mbConfirmation, MB_YESNO) = IDYES;
end;
