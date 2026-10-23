Unicode true
!include "MUI2.nsh"

Name "ANOMALIA - Installation des trois applications"
OutFile "${__FILEDIR__}\..\..\release\Installer-ANOMALIA-3-applications.exe"
BrandingText "ANOMALIA | Installation de la suite"
RequestExecutionLevel user
SetCompressor /SOLID lzma
ShowInstDetails show
InstallDir "$LOCALAPPDATA\ANOMALIA-Suite"

!define MUI_WELCOMEPAGE_TITLE "Installer les trois applications ANOMALIA"
!define MUI_WELCOMEPAGE_TEXT "Ce programme installe automatiquement CMD Studio 0.1.1, ANOMALIA Editor 0.1.1 et ANOMALIA Tools 0.1.1 sur ce compte Windows.$\r$\n$\r$\nIl n'accède pas aux fichiers des autres utilisateurs, ne publie aucune donnée et n'installe aucun service permanent."
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_LANGUAGE "French"

Section "Installer les applications" MainSection
  InitPluginsDir
  SetOutPath "$PLUGINSDIR"
  File "/oname=CMD-Studio-Setup.exe" "${__FILEDIR__}\..\..\installers\studio\CMD Studio Setup 0.1.1.exe"
  File "/oname=ANOMALIA-Editor-Setup.exe" "${__FILEDIR__}\..\..\installers\editor\ANOMALIA Editor Setup 0.1.1.exe"
  File "/oname=ANOMALIA-Tools-Setup.exe" "${__FILEDIR__}\..\..\installers\tools\ANOMALIA Tools Setup 0.1.1.exe"

  DetailPrint "1/3 Installation de CMD Studio 0.1.1..."
  ExecWait '"$PLUGINSDIR\CMD-Studio-Setup.exe" /S' $0
  StrCmp $0 "0" studio_ok
    MessageBox MB_OK|MB_ICONSTOP "L'installation de CMD Studio a echoue (code $0). Les autres applications ne sont pas installees."
    Abort
  studio_ok:

  DetailPrint "2/3 Installation d'ANOMALIA Editor 0.1.1..."
  ExecWait '"$PLUGINSDIR\ANOMALIA-Editor-Setup.exe" /S' $0
  StrCmp $0 "0" editor_ok
    MessageBox MB_OK|MB_ICONSTOP "L'installation d'ANOMALIA Editor a echoue (code $0). CMD Studio peut deja etre installe."
    Abort
  editor_ok:

  DetailPrint "3/3 Installation d'ANOMALIA Tools 0.1.1..."
  ExecWait '"$PLUGINSDIR\ANOMALIA-Tools-Setup.exe" /S' $0
  StrCmp $0 "0" tools_ok
    MessageBox MB_OK|MB_ICONSTOP "L'installation d'ANOMALIA Tools a echoue (code $0). Les installations precedentes ont ete conservees."
    Abort
  tools_ok:
    DetailPrint "Installation terminee : CMD Studio, ANOMALIA Editor, ANOMALIA Tools."
SectionEnd
