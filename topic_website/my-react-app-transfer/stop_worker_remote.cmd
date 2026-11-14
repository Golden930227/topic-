@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop_worker_remote.ps1"
if errorlevel 1 pause
