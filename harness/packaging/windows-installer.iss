; Inno Setup script (run on Windows after tools/build_installer.py). Per-user install: no admin rights.
; Code signing is intentionally not configured (DECISIONS D-19); add SignTool when a certificate exists.
[Setup]
AppName=Harness Designer
AppVersion=0.0.1
DefaultDirName={localappdata}\HarnessDesigner
PrivilegesRequired=lowest
OutputBaseFilename=harness-tool-setup
Compression=lzma2
[Files]
Source: "..\dist\harness-tool\*"; DestDir: "{app}"; Flags: recursesubdirs
[Icons]
Name: "{userprograms}\Harness Designer"; Filename: "{app}\harness-tool.exe"
