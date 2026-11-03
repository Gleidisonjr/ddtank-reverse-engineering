@echo off
title DDTank Clássico - Servidor Dedicado
cd /d "%~dp0"
python src\ddt_cluster_manager.py --no-client
pause
