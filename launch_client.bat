@echo off
chcp 65001 >nul
title DDTank Clássico - Cliente de Jogo
cd /d "%~dp0"
set RUNTIME=runtime\DDClassico.Runtime.exe
set FLASH=runtime\resources\flashver\pepflashplayer64.dll

if not exist "%RUNTIME%" (
    set RUNTIME=..\..\targets\dd-classico\extracted\app\runtime\DDClassico.Runtime.exe
    set FLASH=..\..\targets\dd-classico\extracted\app\runtime\resources\flashver\pepflashplayer64.dll
)

if not exist "%RUNTIME%" (
    echo [-] Executavel local nao encontrado em runtime\DDClassico.Runtime.exe
    pause
    exit /b 1
)

start "" "%~dp0%RUNTIME%" --ppapi-flash-path="%~dp0%FLASH%" --ppapi-flash-version=32.0.0.371 "http://127.0.0.1:8080/player.html"
