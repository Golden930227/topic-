@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_worker_remote.ps1"
if errorlevel 1 goto failed
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_worker_remote.ps1"
if errorlevel 1 goto failed
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_worker_tunnel.ps1"
if errorlevel 1 goto failed
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0publish_worker_entry.ps1"
if errorlevel 1 goto failed
echo WindMind employee remote access started.
exit /b 0
:failed
echo Startup failed. Review the error above and .windmind-logs\remote-*.err.log.
pause
exit /b 1
