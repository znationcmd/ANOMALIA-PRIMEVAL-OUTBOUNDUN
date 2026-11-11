@echo off
setlocal
rem No credentials are embedded, recorded or uploaded by this launcher.
set "ROOT=%~dp0..\.."
set "PROJECT=%ROOT%\unreal\AnomaliaPrimeval.uproject"
set "SCRIPT=%ROOT%\scripts\ue5\sketchfab_import_unreal.py"
if not defined ANOMALIA_SKETCHFAB_STAGING set "ANOMALIA_SKETCHFAB_STAGING=%USERPROFILE%\Downloads\ANOMALIA_Sketchfab_Staging"
echo ANOMALIA - Sketchfab official, licensed 3D model import
where py >nul 2>nul
if %errorlevel% equ 0 (
  py -3 "%ROOT%\scripts\ue5\sketchfab_acquire.py" --download
) else (
  python "%ROOT%\scripts\ue5\sketchfab_acquire.py" --download
)
if errorlevel 1 (
  echo The official download did not complete. Check token and licenses.
  pause
  exit /b 1
)
if not defined UE_EDITOR set "UE_EDITOR=C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
if not exist "%UE_EDITOR%" (
  echo Unreal Editor executable not found at "%UE_EDITOR%".
  echo Set UE_EDITOR to your actual UnrealEditor-Cmd.exe path, then run again.
  pause
  exit /b 2
)
if not exist "%PROJECT%" (
  echo Unreal project not found: "%PROJECT%"
  pause
  exit /b 2
)
echo Importing ONLY authorized downloaded assets to a new Content folder...
"%UE_EDITOR%" "%PROJECT%" -ExecutePythonScript="%SCRIPT%" -unattended -nopause
set "RC=%errorlevel%"
echo Unreal import exited with code %RC%.
echo View local reports in %ANOMALIA_SKETCHFAB_STAGING%.
pause
exit /b %RC%
