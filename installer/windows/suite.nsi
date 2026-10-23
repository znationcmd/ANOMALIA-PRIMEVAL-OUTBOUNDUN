Unicode true
!include "MUI2.nsh"
!ifndef REPO_ROOT
  !error "Passer /DREPO_ROOT=chemin-du-depot a makensis"
!endif

Name "ANOMALIA - Mise a niveau des trois applications"
OutFile "${REPO_ROOT}\release\Mise-a-jour-ANOMALIA-depuis-011.exe"
BrandingText "ANOMALIA | Mise a niveau de 0.1.1"
RequestExecutionLevel user
SetCompressor /SOLID lzma
ShowInstDetails show
InstallDir "$LOCALAPPDATA\ANOMALIA-Suite"

!define MUI_WELCOMEPAGE_TITLE "Mettre a jour les trois applications ANOMALIA"
!define MUI_WELCOMEPAGE_TEXT "Met a niveau tes installations existantes en une seule operation : CMD Studio 0.2.1, ANOMALIA Editor 0.3.0 et ANOMALIA Tools 0.2.0.$\r$\n$\r$\nFerme les trois logiciels au prealable. Les fichiers des projets restent dans leurs dossiers habituels."
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_LANGUAGE "French"

Section "Mettre a jour les applications" MainSection
  InitPluginsDir
  DetailPrint "Mise a niveau par-dessus les installations existantes, sans suppression des dossiers de projets." 
  SetOutPath "$PLUGINSDIR"
  File "/oname=CMD-Studio-Setup.exe" "${REPO_ROOT}\installers\studio\CMD Studio Setup 0.2.1.exe"
  File "/oname=ANOMALIA-Editor-Setup.exe" "${REPO_ROOT}\installers\editor\ANOMALIA Editor Setup 0.3.0.exe"
  File "/oname=ANOMALIA-Tools-Setup.exe" "${REPO_ROOT}\installers\tools\ANOMALIA Tools Setup 0.2.0.exe"

  DetailPrint "1/3 Mise a niveau de CMD Studio vers 0.2.1..."
  ExecWait '"$PLUGINSDIR\CMD-Studio-Setup.exe" /S' $0
  StrCmp $0 "0" studio_ok
    MessageBox MB_OK|MB_ICONSTOP "L'installation de CMD Studio a echoue (code $0). Les autres applications ne sont pas installees."
    Abort
  studio_ok:

  DetailPrint "2/3 Mise a niveau de ANOMALIA Editor vers 0.3.0..."
  ExecWait '"$PLUGINSDIR\ANOMALIA-Editor-Setup.exe" /S' $0
  StrCmp $0 "0" editor_ok
    MessageBox MB_OK|MB_ICONSTOP "L'installation d'ANOMALIA Editor a echoue (code $0). CMD Studio peut deja etre installe."
    Abort
  editor_ok:

  DetailPrint "3/3 Mise a niveau de ANOMALIA Tools vers 0.2.0..."
  ExecWait '"$PLUGINSDIR\ANOMALIA-Tools-Setup.exe" /S' $0
  StrCmp $0 "0" tools_ok
    MessageBox MB_OK|MB_ICONSTOP "L'installation d'ANOMALIA Tools a echoue (code $0). Les installations precedentes ont ete conservees."
    Abort
  tools_ok:
    DetailPrint "Mise a niveau terminee : CMD Studio 0.2.1, ANOMALIA Editor 0.3.0 et ANOMALIA Tools 0.2.0."
SectionEnd
