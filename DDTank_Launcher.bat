@echo off
chcp 65001 >nul
title DDTank Clássico - Servidor ^& Cliente Local
cd /d "%~dp0"
where python >nul 2>nul
if %errorlevel%==0 (
    python src\ddt_cluster_manager.py
) else (
    py -3 src\ddt_cluster_manager.py
)
pause
