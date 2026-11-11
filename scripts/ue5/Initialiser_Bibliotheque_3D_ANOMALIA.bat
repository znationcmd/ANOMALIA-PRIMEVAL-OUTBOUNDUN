@echo off
setlocal EnableExtensions DisableDelayedExpansion
title ANOMALIA - Initialiser la bibliotheque 3D externe
echo.
echo ANOMALIA - Bibliotheque 3D
echo Choisissez un disque ou dossier disponible (idealement SSD externe).
echo Aucune ressource ne sera supprimee, deplacee ou remplacee.
echo.
set "CHOIX="
for /f "usebackq delims=" %%D in (`powershell.exe -NoProfile -STA -Command "Add-Type -AssemblyName System.Windows.Forms; $d=New-Object System.Windows.Forms.FolderBrowserDialog; $d.Description='Choisir le disque ou dossier de la bibliotheque 3D ANOMALIA'; if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { [Console]::WriteLine($d.SelectedPath) }"`) do set "CHOIX=%%D"
if not defined CHOIX (
 echo Aucun dossier selectionne. Rien n'a ete modifie.
 pause
 exit /b 2
)
set "ROOT=%CHOIX%\ANOMALIA_Bibliotheque_3D"
if not exist "%CHOIX%\" (
 echo Le chemin selectionne est inaccessible.
 pause
 exit /b 3
)
for %%D in (
 "01_Originaux\Vehicules"
 "01_Originaux\Personnages_Vetements"
 "01_Originaux\Batiments"
 "01_Originaux\Nature"
 "01_Originaux\Objets"
 "01_Originaux\Textures"
 "02_Licences_Provenance"
 "03_A_Importer"
 "04_Archives_Verifiees"
 "05_Sauvegarde"
) do (
 if not exist "%ROOT%\%%~D" mkdir "%ROOT%\%%~D"
 if errorlevel 1 (
    echo Impossible de preparer : "%ROOT%\%%~D"
    pause
    exit /b 4
 )
)
if not exist "%LOCALAPPDATA%\ANOMALIA" mkdir "%LOCALAPPDATA%\ANOMALIA"
if errorlevel 1 (
 echo Impossible de memoriser le chemin local.
 pause
 exit /b 5
)
powershell.exe -NoProfile -Command "[System.IO.File]::WriteAllText((Join-Path $env:LOCALAPPDATA 'ANOMALIA\bibliotheque-3d-chemin.txt'), $env:ROOT, [System.Text.Encoding]::UTF8)"
echo.
echo Bibliotheque creee : "%ROOT%"
echo Ce script ne copie pas de fichiers et n'importe pas de modeles dans Unreal.
echo Ne supprimez rien du dossier Content d'Unreal.
explorer.exe "%ROOT%"
pause
exit /b 0
