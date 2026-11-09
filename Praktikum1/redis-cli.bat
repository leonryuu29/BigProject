@echo off
chcp 65001 >nul
cd /d "%~dp0"
redis\redis-cli.exe ping >nul 2>&1 || start "Redis" /D "%~dp0redis" redis-server.exe --port 6379 --save ""
redis\redis-cli.exe
