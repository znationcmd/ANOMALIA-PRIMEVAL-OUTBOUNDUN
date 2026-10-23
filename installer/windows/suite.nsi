Unicode true
!include "MUI2.nsh"
!ifndef REPO_ROOT
  !error "Passer /DREPO_ROOT=chemin-du-depot a makensis"
!endif

!define SUITE_VERSION "1.0.0"
!define CMD_VERSION "0.2.1"
!define EDITOR_VERSION "0.5.1"
!define TOOLS_VERSION "0.2.2"

Name "ANOMALIA - Les trois logiciels, une installation"
OutFile "${REPO_ROOT}\release\Installer-ANOMALIA-Trois-Applications-AutoMAJ.exe"
BrandingText "ANOMALIA / CMD - Installation unique"
RequestExecutionLevel user
SetCompressor /SOLID lzma
ShowInstDetails show
InstallDir "$LOCALAPPDATA\ANOMALIA-Suite"

VIProductVersion "1.0.0.0"
VIAddVersionKey "ProductName" "ANOMALIA - Installation des trois logiciels"
VIAddVersionKey "FileDescription" "CMD Studio + ANOMALIA Editor + ANOMALIA Tools"
VIAddVersionKey "FileVersion" "${SUITE_VERSION}"
VIAddVersionKey "ProductVersion" "${SUITE_VERSION}"
VIAddVersionKey "CompanyName" "CMD / ANOMALIA"

!define MUI_WELCOMEPAGE_TITLE "Trois applications ANOMALIA, un seul installateur"
!define MUI_WELCOMEPAGE_TEXT "Cette installation met a niveau CMD Studio ${CMD_VERSION}, ANOMALIA Editor ${EDITOR_VERSION} et ANOMALIA Tools ${TOOLS_VERSION} en une seule operation.$\r$\n$\r$\nLes projets, ressources et configurations utilisateur existants sont conserves. Ferme les trois programmes avant de continuer.$\r$\n$\r$\nEditor et Tools recevront ensuite leurs futures versions par leur canal de mises a jour. CMD Studio conserve un canal PRIVE, a configurer dans son application."
!define MUI_FINISHPAGE_TITLE "Les trois logiciels sont installes"
!define MUI_FINISHPAGE_TEXT "CMD Studio, ANOMALIA Editor et ANOMALIA Tools ont ete installes ou mis a niveau. Aucune donne utilisateur n'a ete supprimee. Les mises a jour automatiques d'Editor et Tools sont integrees ; celles de CMD Studio demandent l'activation de sa source privee."
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_LANGUAGE "French"

Section "Installer les trois applications" MainSection
  InitPluginsDir
  SetOutPath "$PLUGINSDIR"
  File "/oname=CMD-Studio-Setup.exe" "${REPO_ROOT}\installers\studio\CMD-Studio-Setup.exe"
  File "/oname=ANOMALIA-Editor-Setup.exe" "${REPO_ROOT}\installers\editor\ANOMALIA-Editor-Setup.exe"
  File "/oname=ANOMALIA-Tools-Setup.exe" "${REPO_ROOT}\installers\tools\ANOMALIA-Tools-Setup.exe"

  DetailPrint "1/3 CMD Studio ${CMD_VERSION} : mise a niveau de l'application existante..."
  ExecWait '"$PLUGINSDIR\CMD-Studio-Setup.exe" /S' $0
  StrCmp $0 "0" studio_ok
    MessageBox MB_ICONSTOP|MB_OK "CMD Studio : code de sortie $0. Les fichiers utilisateur sont conserves ; les deux autres logiciels ne sont pas modifies."
    Abort
  studio_ok:

  DetailPrint "2/3 ANOMALIA Editor ${EDITOR_VERSION} : activation des mises a jour automatiques..."
  ExecWait '"$PLUGINSDIR\ANOMALIA-Editor-Setup.exe" /S' $0
  StrCmp $0 "0" editor_ok
    MessageBox MB_ICONSTOP|MB_OK "ANOMALIA Editor : code de sortie $0. CMD Studio peut deja avoir ete mis a niveau. Les projets restent conserves."
    Abort
  editor_ok:

  DetailPrint "3/3 ANOMALIA Tools ${TOOLS_VERSION} : activation des mises a jour automatiques..."
  ExecWait '"$PLUGINSDIR\ANOMALIA-Tools-Setup.exe" /S' $0
  StrCmp $0 "0" tools_ok
    MessageBox MB_ICONSTOP|MB_OK "ANOMALIA Tools : code de sortie $0. Les applications precedentes sont conservees et les projets ne sont pas effaces."
    Abort
  tools_ok:
    DetailPrint "Succes : CMD Studio ${CMD_VERSION}, ANOMALIA Editor ${EDITOR_VERSION}, ANOMALIA Tools ${TOOLS_VERSION}."
    DetailPrint "Editor et Tools se mettront a jour via les publications officielles lors des prochains lancements."
    DetailPrint "CMD Studio : ouvrir Parametres > Mises a jour et configurer la source HTTPS privee."
SectionEnd
