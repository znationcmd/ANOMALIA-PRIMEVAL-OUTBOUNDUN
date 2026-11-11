@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0open-archipelago-world.ps1"
if errorlevel 1 pause
