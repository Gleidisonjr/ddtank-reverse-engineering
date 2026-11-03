#!/usr/bin/env python3
"""
District 187 (S2 Rebirth) — Native Control Center & Launcher
Allows toggling Ultra HD textures, switching servers (Online/Offline),
configuring engine parameters (FPS uncap, language, resolutions),
fetching live community telemetry, and launching the original LithTech executable.

Author: Gleidison Carvalho (2026-11-02)
"""

import os
import sys
import json
import ssl
import subprocess
import threading
import urllib.request
import tkinter as tk
from tkinter import ttk, messagebox

sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CLIENT_DIR = os.path.join(ROOT_DIR, 'targets', 'district-187', 'client-rebirth')
ARCHCFG_PATH = os.path.join(CLIENT_DIR, 'Default.archcfg')
SETTINGS_PATH = os.path.join(CLIENT_DIR, 'settings.cfg')
AUTOEXEC_PATH = os.path.join(CLIENT_DIR, 'autoexec.cfg')
PAKET_PATH = os.path.join(CLIENT_DIR, '.launcher', 'paket.json')
EXEPATH = os.path.join(CLIENT_DIR, 'TheRaw.exe')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

class D187LauncherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("District 187: Sin Streets — Native Control Center")
        self.root.geometry("640x680")
        self.root.resizable(False, False)
        self.root.configure(bg="#18191c")

        # Variables
        self.mode_var = tk.StringVar(value="online")
        self.map_var = tk.StringVar(value="twoway")
        self.hd_var = tk.BooleanVar(value=True)
        self.lang_var = tk.StringVar(value="en")
        self.fps_var = tk.StringVar(value="0 (Unlimited 144+)")
        self.res_var = tk.StringVar(value="1920x1080")
        self.telemetry_text = tk.StringVar(value="Carregando telemetria ao vivo da comunidade...")

        self.setup_styles()
        self.build_ui()
        self.load_current_configs()
        
        # Start telemetry worker
        threading.Thread(target=self.fetch_telemetry, daemon=True).start()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#18191c')
        style.configure('TLabel', background='#18191c', foreground='#e0e0e0', font=('Segoe UI', 10))
        style.configure('Header.TLabel', background='#18191c', foreground='#00adb5', font=('Segoe UI', 15, 'bold'))
        style.configure('SubHeader.TLabel', background='#18191c', foreground='#aaaaaa', font=('Segoe UI', 9))
        style.configure('Section.TLabelframe', background='#222831', foreground='#00adb5')
        style.configure('Section.TLabelframe.Label', background='#222831', foreground='#00adb5', font=('Segoe UI', 10, 'bold'))
        style.configure('TRadiobutton', background='#222831', foreground='#eeeeee', font=('Segoe UI', 10))
        style.configure('TCheckbutton', background='#222831', foreground='#eeeeee', font=('Segoe UI', 10))
        style.configure('TCombobox', fieldbackground='#2d3238', background='#393e46', foreground='#ffffff')

    def build_ui(self):
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title Banner
        title_lbl = ttk.Label(main_frame, text="DISTRICT 187: SIN STREETS", style='Header.TLabel')
        title_lbl.pack(anchor='w')
        sub_lbl = ttk.Label(main_frame, text="LithTech Jupiter EX Engine • Native Control Center & Preset Manager", style='SubHeader.TLabel')
        sub_lbl.pack(anchor='w', pady=(0, 15))

        # 1. Server Environment Box
        server_box = ttk.LabelFrame(main_frame, text=" 1. Ambiente de Servidor & Conexão ", style='Section.TLabelframe', padding="10")
        server_box.pack(fill=tk.X, pady=5)

        ttk.Radiobutton(server_box, text="Servidor Oficial da Comunidade (Online • 179.61.147.154:12000)", variable=self.mode_var, value="online").pack(anchor='w', pady=2)
        ttk.Radiobutton(server_box, text="Emulador / Servidor Local Offline (Preservação • 127.0.0.1:12000)", variable=self.mode_var, value="offline").pack(anchor='w', pady=2)

        row_map = ttk.Frame(server_box, style='TFrame')
        row_map.pack(fill=tk.X, pady=(6, 2))
        ttk.Label(row_map, text="Mapa Ativo (Offline/Emulador):").pack(side=tk.LEFT, padx=(0, 10))
        map_cb = ttk.Combobox(row_map, textvariable=self.map_var, values=["twoway (Demolition)", "Arrival (TDM)", "thebank (Gold Heist)", "oldtown (TDM)", "10025_Heaven (Demolition)"], state="readonly", width=26)
        map_cb.pack(side=tk.LEFT)

        # 2. Engine & Graphics Config Box
        engine_box = ttk.LabelFrame(main_frame, text=" 2. Configurações de Motor & Gráficos ", style='Section.TLabelframe', padding="10")
        engine_box.pack(fill=tk.X, pady=5)

        hd_check = ttk.Checkbutton(engine_box, text="Ativar Texturas Ultra HD 2K/4K (Volumes HD1 a HD6 montados)", variable=self.hd_var, command=self.apply_engine_configs)
        hd_check.pack(anchor='w', pady=3)

        # Language row
        row1 = ttk.Frame(engine_box, style='TFrame')
        row1.pack(fill=tk.X, pady=3)
        ttk.Label(row1, text="Idioma dos Textos e Vozes:").pack(side=tk.LEFT, padx=(0, 10))
        lang_cb = ttk.Combobox(row1, textvariable=self.lang_var, values=["en (Inglês Oficial)", "tr (Turco)"], state="readonly", width=18)
        lang_cb.pack(side=tk.LEFT)
        lang_cb.bind("<<ComboboxSelected>>", lambda e: self.apply_engine_configs())

        # FPS row
        row2 = ttk.Frame(engine_box, style='TFrame')
        row2.pack(fill=tk.X, pady=3)
        ttk.Label(row2, text="Limite de Taxa de Quadros (FPS):").pack(side=tk.LEFT, padx=(0, 10))
        fps_cb = ttk.Combobox(row2, textvariable=self.fps_var, values=["0 (Unlimited 144+)", "60 FPS (V-Sync)", "144 FPS", "240 FPS"], state="readonly", width=18)
        fps_cb.pack(side=tk.LEFT)
        fps_cb.bind("<<ComboboxSelected>>", lambda e: self.apply_engine_configs())

        # Resolution row
        row3 = ttk.Frame(engine_box, style='TFrame')
        row3.pack(fill=tk.X, pady=3)
        ttk.Label(row3, text="Resolução Nativa Recomendada:").pack(side=tk.LEFT, padx=(0, 10))
        res_cb = ttk.Combobox(row3, textvariable=self.res_var, values=["1920x1080 (Full HD)", "2560x1440 (2K QHD)", "1280x720 (HD)"], state="readonly", width=18)
        res_cb.pack(side=tk.LEFT)
        res_cb.bind("<<ComboboxSelected>>", lambda e: self.apply_engine_configs())

        # 3. Community Live Telemetry Box
        telemetry_box = ttk.LabelFrame(main_frame, text=" 3. Telemetria da Comunidade ao Vivo ", style='Section.TLabelframe', padding="10")
        telemetry_box.pack(fill=tk.X, pady=5)

        self.telemetry_lbl = tk.Label(telemetry_box, textvariable=self.telemetry_text, justify=tk.LEFT, bg="#222831", fg="#00adb5", font=('Consolas', 9))
        self.telemetry_lbl.pack(anchor='w')

        # 4. Action Launch Button
        btn_frame = ttk.Frame(main_frame, style='TFrame')
        btn_frame.pack(fill=tk.X, pady=(15, 0))

        launch_btn = tk.Button(
            btn_frame,
            text="▶ INICIAR DISTRICT 187 NATIVO (TheRaw.exe)",
            font=('Segoe UI', 12, 'bold'),
            bg="#00adb5",
            fg="#ffffff",
            activebackground="#008085",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=10,
            pady=12,
            cursor="hand2",
            command=self.launch_game
        )
        launch_btn.pack(fill=tk.X)

    def load_current_configs(self):
        # Check Default.archcfg for HD
        if os.path.exists(ARCHCFG_PATH):
            with open(ARCHCFG_PATH, 'r', encoding='utf-8') as f:
                content = f.read()
                self.hd_var.set("HD1.Res00" in content)

    def apply_engine_configs(self):
        # 1. Update Default.archcfg for HD
        lines = [
            r"game\Game.Res00",
            r"game\Update_1.Res00",
            r"game\Update_2.Res00"
        ]
        if self.hd_var.get():
            for i in range(1, 7):
                lines.append(rf"game\HD{i}.Res00")

        with open(ARCHCFG_PATH, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

        # 2. Update paket.json
        lang_code = "en" if "en" in self.lang_var.get() else "tr"
        paket_mode = "hd" if self.hd_var.get() else "normal"
        os.makedirs(os.path.dirname(PAKET_PATH), exist_ok=True)
        with open(PAKET_PATH, 'w', encoding='utf-8') as f:
            json.dump({"paket": paket_mode, "dil": lang_code}, f, indent=2)

        # 3. Update settings.cfg & autoexec.cfg for FPS
        fps_val = "0"
        if "60" in self.fps_var.get(): fps_val = "60"
        elif "144" in self.fps_var.get(): fps_val = "144"
        elif "240" in self.fps_var.get(): fps_val = "240"

        with open(AUTOEXEC_PATH, 'w', encoding='utf-8') as f:
            f.write(f"MaxFPS {fps_val}\nShowFrameRate 1\nGraphicQualityLevel 3\nBindTexturesMipOffset 0\n")

    def fetch_telemetry(self):
        try:
            req = urllib.request.Request('https://s2rebirth.com/api/oyuncu/siralama', headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                players = data.get('toplamOyuncu', 0)
                clans = data.get('toplamKlan', 0)
                matches = data.get('maclar', [])
                last_m_str = "Nenhuma partida recente"
                if matches:
                    m = matches[0]
                    last_m_str = f"{m.get('haritaAd')} ({m.get('modAd')}) • {m.get('skor1')}:{m.get('skor2')} • MVP: {m.get('mvp')}"

                summary = (
                    f"Jogadores Registrados: {players:,} | Clãs Ativos: {clans}\n"
                    f"Última Partida Dedicada: {last_m_str}\n"
                    f"Status Servidor: ONLINE (Comunidade S2 Rebirth Ativa)"
                )
                self.telemetry_text.set(summary)
        except Exception as e:
            self.telemetry_text.set("Modo Offline / Sem conexão com a API de telemetria da comunidade.")

    def launch_game(self):
        self.apply_engine_configs()
        env = os.environ.copy()
        env['__COMPAT_LAYER'] = 'RunAsInvoker'

        if self.mode_var.get() == "online":
            target_bat = os.path.join(ROOT_DIR, 'launch_s2rebirth_direct.bat')
            cmd = ['cmd.exe', '/c', target_bat]
        else:
            target_bat = os.path.join(ROOT_DIR, 'launch_offline_emulator.bat')
            cmd = ['cmd.exe', '/c', target_bat]

        try:
            subprocess.Popen(cmd, cwd=ROOT_DIR, env=env)
            messagebox.showinfo("Sucesso", "O cliente original TheRaw.exe foi disparado com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro de Inicialização", f"Falha ao executar o cliente nativo: {e}")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--cli':
        print("[*] District 187 Native Control Center (CLI Mode)")
        print(f"    Client Root: {CLIENT_DIR}")
        print(f"    Executable:  {EXEPATH} (Exists: {os.path.exists(EXEPATH)})")
        print(f"    ArchConfig:  {ARCHCFG_PATH} (Exists: {os.path.exists(ARCHCFG_PATH)})")
        return

    root = tk.Tk()
    app = D187LauncherApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
