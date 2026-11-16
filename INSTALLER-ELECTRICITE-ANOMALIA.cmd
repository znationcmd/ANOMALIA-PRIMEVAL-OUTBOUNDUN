@echo off
setlocal
title ANOMALIA'Z - Installation electrique UE5
echo.
echo ANOMALIA'Z PRIGIMALIA - INSTALLATION REFRIGERATEUR / GENERATEUR / BATTERIE / PROJECTEURS
echo.
echo Ce programme sauvegarde les sources avant toute modification,
echo refuse les conflits avec les versions locales et tente de compiler dans UE5.
echo Aucun jeu installe ou sauvegarde de joueurs ne sera supprime.
echo.
set "INSTALL_SCRIPT=%TEMP%\Install-Anomalia-Electricite.ps1"
powershell.exe -NoProfile -Command "$ErrorActionPreference='Stop'; Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/02604e2fd4c53958adbf5c305d5fbacd0eecc10a/scripts/ue5/Install-Anomalia-Electricite.ps1' -OutFile '%INSTALL_SCRIPT%'"
if errorlevel 1 (
  echo ERREUR DE TELECHARGEMENT. Rien n'a ete modifie.
  pause
  exit /b 1
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%INSTALL_SCRIPT%"
if errorlevel 1 (
  echo.
  echo INSTALLATION NON TERMINEE. Voir journal indique ci-dessus.
  pause
  exit /b 1
)
echo.
echo Sources installees dans le projet UE5 si compatible.
echo Le jeu Windows empaquete et les vrais objets des cartes restent a verifier.
pause
endlocal
