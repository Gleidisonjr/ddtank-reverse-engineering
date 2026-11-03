"""
Build DDTank Friends Multiplayer Distribution Pack
Target: DDClássico (ddclassico.com) v2.0.5 / 7Road DDTank Engine
Builds a portable, lightweight zip package in dist/ ready to be shared with friends
to play online via Tailscale VPN.
"""

import os
import shutil
import zipfile

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DIST_DIR = os.path.join(BASE_DIR, 'dist', 'DDTank_Amigos')
RUNTIME_SRC = os.path.join(BASE_DIR, 'runtime')
if not os.path.exists(RUNTIME_SRC):
    RUNTIME_SRC = os.path.join(BASE_DIR, '..', '..', 'targets', 'dd-classico', 'extracted', 'app', 'runtime')
ZIP_OUT = os.path.join(BASE_DIR, 'dist', 'DDTank_Multiplayer_Amigos.zip')

def clean_and_prepare():
    if os.path.exists(DIST_DIR):
        shutil.rmtree(DIST_DIR)
    os.makedirs(DIST_DIR, exist_ok=True)
    print(f"[+] Prepared directory {DIST_DIR}")

def copy_runtime_files():
    print("[*] Copying decoupled Electron runtime and Flash Player...")
    essential_files = [
        'DDClassico.Runtime.exe',
        'ffmpeg.dll',
        'icudtl.dat',
        'v8_context_snapshot.bin',
        'snapshot_blob.bin',
        'natives_blob.bin',
    ]
    for f in essential_files:
        src = os.path.join(RUNTIME_SRC, f)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(DIST_DIR, f))

    # Copy resources folder (custom app/ and flashver/pepflashplayer64.dll)
    res_dest = os.path.join(DIST_DIR, 'resources')
    os.makedirs(res_dest, exist_ok=True)
    
    # Custom app bypass folder
    app_src = os.path.join(RUNTIME_SRC, 'resources', 'app')
    if os.path.exists(app_src):
        shutil.copytree(app_src, os.path.join(res_dest, 'app'), dirs_exist_ok=True)
    
    # Flash Pepper DLL
    flash_src = os.path.join(RUNTIME_SRC, 'resources', 'flashver')
    if os.path.exists(flash_src):
        shutil.copytree(flash_src, os.path.join(res_dest, 'flashver'), dirs_exist_ok=True)

    print(f"[+] Decoupled client binaries copied to {DIST_DIR}")

def create_launcher_scripts():
    launcher_bat = """@echo off
title DDTank Multiplayer - Conectar ao Servidor
color 0b
cls
echo ==================================================================
echo         DDTANK CLÁSSICO - CLIENTE MULTIPLAYER (AMIGOS)            
echo ==================================================================
echo.
set /p SERVER_IP="Digite o IP Tailscale do Servidor (Enter para 127.0.0.1): "
if "%SERVER_IP%"=="" set SERVER_IP=127.0.0.1

echo.
echo [*] Conectando ao servidor em: http://%SERVER_IP%:8080/player.html ...
echo [*] Inicializando Adobe Flash Pepper PPAPI v32.0.0.371...

start "" "%~dp0DDClassico.Runtime.exe" ^
    --ppapi-flash-path="%~dp0resources\\flashver\\pepflashplayer64.dll" ^
    --ppapi-flash-version=32.0.0.371 ^
    "http://%SERVER_IP%:8080/player.html"

echo.
echo [OK] Jogo iniciado com sucesso! Divirtam-se!
timeout /t 3 >nul
exit
"""
    bat_path = os.path.join(DIST_DIR, 'Jogar_Online.bat')
    with open(bat_path, 'w', encoding='utf-8') as f:
        f.write(launcher_bat)
    print(f"[+] Created {bat_path}")

def create_readme():
    readme = """==================================================================
           DDTANK CLÁSSICO MULTIPLAYER - GUIA DE INSTALAÇÃO       
==================================================================

COMO JOGAR COM SEUS AMIGOS ONLINE (VIA TAILSCALE VPN):

1. INSTALAR O TAILSCALE:
   - Baixe e instale o Tailscale gratuitamente em: https://tailscale.com/
   - Crie uma conta ou faça login.
   - Entre na mesma rede virtual (Tailnet) do Host / Servidor.

2. PEGAR O IP DO SERVIDOR:
   - Peça ao Host o IP Tailscale da máquina dele (ex: 100.85.120.45).

3. INICIAR O JOGO:
   - Dê um duplo-clique no arquivo "Jogar_Online.bat".
   - Digite o IP do Servidor quando solicitado e aperte ENTER.
   - O jogo abrirá direto no Flash Player com 60 FPS, sem necessidade de navegadores antigos.

4. DENTRO DO JOGO:
   - Escolha seu apelido ou conecte-se no Canal 1 (Lobby).
   - Entre na sala criada pelo Host ou crie sua própria sala!
   - Mochila e Arsenal VIP com armas lendárias (+12) disponíveis para todos!

Bom jogo!
"""
    readme_path = os.path.join(DIST_DIR, 'README_COMO_JOGAR.txt')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme)
    print(f"[+] Created {readme_path}")

def create_zip():
    print(f"[*] Packaging {ZIP_OUT}...")
    with zipfile.ZipFile(ZIP_OUT, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(DIST_DIR):
            for file in files:
                abs_p = os.path.join(root, file)
                rel_p = os.path.relpath(abs_p, os.path.dirname(DIST_DIR))
                z.write(abs_p, rel_p)
    sz_mb = os.path.getsize(ZIP_OUT) / (1024 * 1024)
    print(f"[SUCCESS] Generated {ZIP_OUT} ({sz_mb:.2f} MB)")

if __name__ == '__main__':
    print("[*] Building DDTank Friends Multiplayer Distribution Pack...")
    clean_and_prepare()
    copy_runtime_files()
    create_launcher_scripts()
    create_readme()
    create_zip()
    print("[+] Distribution pack build complete!")
