"""
DDTank Cluster & Daemon Manager
Target: DDClássico (ddclassico.com) v2.0.5 / 7Road DDTank Engine
Orchestrates:
  1. Flash Socket Policy Server (TCP 843)
  2. Local CDN & Static Asset Web Server (HTTP 8080)
  3. DDTank Game Core Server (TCP 9200)
  4. Electron Desktop Client (DDClassico.Runtime.exe)
"""

import subprocess
import threading
import socket
import time
import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RUNTIME_EXE = os.path.join(BASE_DIR, 'runtime', 'DDClassico.Runtime.exe')
if not os.path.exists(RUNTIME_EXE):
    RUNTIME_EXE = os.path.join(BASE_DIR, '..', '..', 'targets', 'dd-classico', 'extracted', 'app', 'runtime', 'DDClassico.Runtime.exe')
FLASH_DLL = os.path.join(BASE_DIR, 'runtime', 'resources', 'flashver', 'pepflashplayer64.dll')
if not os.path.exists(FLASH_DLL):
    FLASH_DLL = os.path.join(BASE_DIR, '..', '..', 'targets', 'dd-classico', 'extracted', 'app', 'runtime', 'resources', 'flashver', 'pepflashplayer64.dll')


def get_tailscale_ip():
    try:
        out = subprocess.check_output(['tailscale', 'ip', '-4'], stderr=subprocess.DEVNULL)
        return out.decode().strip()
    except Exception:
        try:
            for info in socket.getaddrinfo(socket.gethostname(), None):
                ip = info[4][0]
                if ip.startswith("100."):
                    return ip
        except Exception:
            pass
    return None


class DDTCluster:
    def __init__(self):
        self.procs = {}

    def start_services(self):
        print("==================================================================")
        print("         DDTANK LOCAL CLUSTER & EMULATOR ORCHESTRATOR             ")
        print("==================================================================")
        ts_ip = get_tailscale_ip()
        if ts_ip:
            print(f"[+] Tailscale IP Detected: {ts_ip}")
            print(f"[+] Share this URL with your friends: http://{ts_ip}:8080/player.html")
        else:
            print("[*] Tailscale not detected or offline (Running in Localhost mode)")
            print("[+] Local URL: http://127.0.0.1:8080/player.html")

        # 1. Start Policy Server (TCP 843)
        print("\n[*] Starting Flash Policy Server (TCP 843)...")
        p_script = os.path.join(os.path.dirname(__file__), 'ddt_policy_server.py')
        self.procs['policy'] = subprocess.Popen([sys.executable, p_script])

        # 2. Start CDN Asset Server (HTTP 8080)
        print("[*] Starting Local Asset CDN Server (HTTP 8080)...")
        cdn_script = os.path.join(os.path.dirname(__file__), 'ddt_local_cdn.py')
        self.procs['cdn'] = subprocess.Popen([sys.executable, cdn_script])

        # 3. Start Game Core Server (TCP 9200)
        print("[*] Starting DDTank Game Core Server (TCP 9200)...")
        game_script = os.path.join(os.path.dirname(__file__), 'ddt_server.py')
        self.procs['game'] = subprocess.Popen([sys.executable, game_script])

        time.sleep(1.5)
        print("\n[+] All 3 Daemons are Active and Ready!")

    def launch_client(self):
        if not os.path.exists(RUNTIME_EXE):
            print(f"[-] Runtime executable not found at {RUNTIME_EXE}")
            return

        print(f"\n[*] Launching DDTank Desktop Client...")
        client_env = os.environ.copy()
        client_env['DDT_SERVER_URL'] = 'http://127.0.0.1:8080/player.html'
        
        args = [
            RUNTIME_EXE,
            f'--ppapi-flash-path={FLASH_DLL}',
            '--ppapi-flash-version=32.0.0.371',
            'http://127.0.0.1:8080/player.html'
        ]
        self.procs['client'] = subprocess.Popen(args, env=client_env)
        print(f"[+] Desktop Client Launched (PID: {self.procs['client'].pid})!")

    def wait(self):
        print("\n[+] Cluster is running. Press Ctrl+C to gracefully stop all services.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_all()

    def stop_all(self):
        print("\n[*] Stopping all cluster services...")
        for name, proc in self.procs.items():
            try:
                proc.terminate()
                print(f"  [+] Stopped {name}")
            except Exception:
                pass
        print("[+] Cluster stopped cleanly.")


if __name__ == '__main__':
    cluster = DDTCluster()
    cluster.start_services()
    if '--no-client' not in sys.argv:
        cluster.launch_client()
    cluster.wait()
