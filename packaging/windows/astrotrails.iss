; SPDX-License-Identifier: GPL-3.0-or-later
; Inno Setup 6 script — run *after* PyInstaller has populated dist\.
; Produces AstrotrailsSetup.exe with Start Menu shortcuts + uninstaller.

#define MyAppName       "astrotrails"
#define MyAppPublisher  "Theodoros Gatsios"
#define MyAppURL        "https://github.com/theogatsios/astrotrails"
; Version is injected by the release workflow; fall back to a placeholder.
#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif
#define MyGuiExe  "astrotrails-" + MyAppVersion + "-win64.exe"
#define MyCliExe  "astrotrails-" + MyAppVersion + "-win64-cli.exe"

[Setup]
AppId={{D2F8E3B1-2F8A-4A63-9F9B-9B2F8A4A63D2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=..\..\LICENSE.txt
OutputDir=.
OutputBaseFilename=AstrotrailsSetup-{#MyAppVersion}
SetupIconFile=..\assets\astrotrails.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "..\..\dist\{#MyGuiExe}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\dist\{#MyCliExe}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyGuiExe}"
Name: "{autoprograms}\{#MyAppName} (CLI)"; Filename: "{app}\{#MyCliExe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyGuiExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyGuiExe}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
