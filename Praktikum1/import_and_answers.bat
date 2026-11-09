@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
if not exist results mkdir results
redis\redis-cli.exe ping >nul 2>&1 || start "Redis" /D "%~dp0redis" redis-server.exe --port 6379 --save ""
timeout /t 2 >nul
echo [1/2] Import von data\business.json (ca. 1 Minute) ...
python load_data.py data\business.json --flush > results\import_local.txt 2>&1
type results\import_local.txt
echo [2/2] Antworten ...
python answers.py > results\antworten_local.txt 2>&1
type results\antworten_local.txt
echo.
echo Fertig. Ergebnisse in results\
pause
