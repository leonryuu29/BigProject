@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist results mkdir results
echo Deployment der Praktikum-Umgebung (Log: results\deploy_log.txt)
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Transcript -Path 'results\deploy_log.txt' -Force | Out-Null; try { & '.\scripts\run_portable.ps1' } catch { Write-Host ('FEHLER: ' + $_) } finally { Stop-Transcript | Out-Null }"
echo.
pause
