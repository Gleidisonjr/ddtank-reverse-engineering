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
import json
import time
import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RUNTIME_DIR = os.path.join(BASE_DIR, 'runtime')
if not os.path.exists(os.path.join(RUNTIME_DIR, 'DDClassico.Runtime.exe')):
    alt_runtime = os.path.join(BASE_DIR, '..', '..', 'targets', 'dd-classico', 'extracted', 'app', 'runtime')
    if os.path.exists(os.path.join(alt_runtime, 'DDClassico.Runtime.exe')):
        RUNTIME_DIR = alt_runtime

RUNTIME_EXE = os.path.join(RUNTIME_DIR, 'DDClassico.Runtime.exe')
FLASH_DLL = os.path.join(RUNTIME_DIR, 'resources', 'flashver', 'pepflashplayer64.dll')


ELECTRON_BYPASS_MAIN_JS = """'use strict';

const { app, BrowserWindow } = require('electron');
const path = require('path');
const fs = require('fs');

function resolveFlashPath() {
  for (const arg of process.argv) {
    if (arg.startsWith('--ppapi-flash-path=')) {
      const candidate = arg.slice('--ppapi-flash-path='.length).replace(/^"|"$/g, '');
      if (candidate && fs.existsSync(candidate)) {
        return candidate;
      }
    }
  }
  return path.join(process.resourcesPath, 'flashver', 'pepflashplayer64.dll');
}

function resolveTargetUrl() {
  for (const arg of process.argv.slice(1)) {
    const clean = arg.replace(/^"|"$/g, '');
    if (/^https?:\\/\\//i.test(clean)) {
      return clean;
    }
  }
  return process.env.DDT_SERVER_URL || 'http://127.0.0.1:8080/player.html';
}

const flashPath = resolveFlashPath();
app.commandLine.appendSwitch('ppapi-flash-path', flashPath);
app.commandLine.appendSwitch('ppapi-flash-version', '32.0.0.371');
app.commandLine.appendSwitch('autoplay-policy', 'no-user-gesture-required');

let mainWindow = null;

function createWindow() {
  const iconPath = path.join(process.resourcesPath, 'icon.ico');
  mainWindow = new BrowserWindow({
    width: 1000,
    height: 600,
    useContentSize: true,
    resizable: true,
    autoHideMenuBar: true,
    backgroundColor: '#000000',
    title: 'DDTank Clássico - Servidor & Cliente Local',
    icon: fs.existsSync(iconPath) ? iconPath : undefined,
    webPreferences: {
      plugins: true,
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.setMenuBarVisibility(false);

  mainWindow.webContents.on('before-input-event', (event, input) => {
    if (
      input.type === 'keyDown' &&
      (input.key === 'F12' || (input.control && input.shift && input.key.toLowerCase() === 'i'))
    ) {
      mainWindow.webContents.toggleDevTools();
      event.preventDefault();
    } else if (input.type === 'keyDown' && input.key === 'F5') {
      mainWindow.webContents.reloadIgnoringCache();
      event.preventDefault();
    }
  });

  mainWindow.loadURL(resolveTargetUrl());

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  app.quit();
});
"""


def ensure_decoupled_electron_app():
    """Ensures runtime/resources/app bypass exists and removes locked app.asar if present."""
    resources_dir = os.path.join(RUNTIME_DIR, 'resources')
    if not os.path.isdir(resources_dir):
        return

    asar_file = os.path.join(resources_dir, 'app.asar')
    if os.path.exists(asar_file):
        try:
            os.remove(asar_file)
            print("[+] Removed protected app.asar (decoupling Themida native check)")
        except OSError:
            pass

    app_dir = os.path.join(resources_dir, 'app')
    pkg_json = os.path.join(app_dir, 'package.json')
    main_js = os.path.join(app_dir, 'main.js')

    if not os.path.exists(pkg_json) or not os.path.exists(main_js):
        os.makedirs(app_dir, exist_ok=True)
        with open(pkg_json, 'w', encoding='utf-8') as f:
            json.dump({
                "name": "ddtank-local-client",
                "productName": "DDTank Clássico",
                "version": "2.0.5",
                "main": "main.js"
            }, f, indent=2, ensure_ascii=False)
        with open(main_js, 'w', encoding='utf-8') as f:
            f.write(ELECTRON_BYPASS_MAIN_JS)
        print(f"[+] Initialized decoupled Electron app in {app_dir}")


def wait_for_port(host: str, port: int, timeout: float = 8.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.15)
    return False


def cleanup_stale_python_ports(ports):
    """Terminates orphaned Python server processes holding DDTank TCP ports on Windows."""
    if sys.platform != 'win32':
        return
    my_pid = os.getpid()
    port_suffixes = tuple(f':{p}' for p in ports)
    try:
        out = subprocess.check_output(['netstat', '-ano', '-p', 'tcp'], stderr=subprocess.DEVNULL).decode('latin1', errors='ignore')
    except Exception:
        return

    pids = set()
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 5 and parts[0].upper() == 'TCP':
            if parts[1].endswith(port_suffixes) and parts[2].endswith(':0'):
                try:
                    pid = int(parts[-1])
                    if pid > 4 and pid != my_pid:
                        pids.add(pid)
                except ValueError:
                    pass

    killed_any = False
    for pid in pids:
        try:
            cmd_out = subprocess.check_output(
                [
                    'powershell', '-NoProfile', '-Command',
                    f"(Get-CimInstance Win32_Process -Filter 'ProcessId={pid}').CommandLine"
                ],
                stderr=subprocess.DEVNULL
            ).decode('utf-8', errors='ignore').strip().lower()
            if 'ddt_' in cmd_out:
                print(f"[*] Stopping previous DDTank server daemon (PID {pid})...")
                subprocess.run(['taskkill', '/F', '/PID', str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                killed_any = True
        except Exception:
            pass

    if killed_any:
        time.sleep(0.5)


def is_port_available(port: int, host: str = '0.0.0.0') -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        if sys.platform == 'win32' and hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
            s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        elif sys.platform != 'win32':
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def find_available_port(preferred: int, max_tries: int = 20) -> int:
    for p in range(preferred, preferred + max_tries):
        if is_port_available(p):
            return p
    return preferred


def create_windows_job_object():
    """Creates a Windows Job Object that kills child daemons if the console window is closed."""
    if sys.platform != 'win32':
        return None
    try:
        import ctypes
        from ctypes import wintypes

        class IO_COUNTERS(ctypes.Structure):
            _fields_ = [
                ('ReadOperationCount', ctypes.c_uint64),
                ('WriteOperationCount', ctypes.c_uint64),
                ('OtherOperationCount', ctypes.c_uint64),
                ('ReadTransferCount', ctypes.c_uint64),
                ('WriteTransferCount', ctypes.c_uint64),
                ('OtherTransferCount', ctypes.c_uint64),
            ]

        class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ('PerProcessUserTimeLimit', ctypes.c_int64),
                ('PerJobUserTimeLimit', ctypes.c_int64),
                ('LimitFlags', wintypes.DWORD),
                ('MinimumWorkingSetSize', ctypes.c_size_t),
                ('MaximumWorkingSetSize', ctypes.c_size_t),
                ('ActiveProcessLimit', wintypes.DWORD),
                ('Affinity', ctypes.c_size_t),
                ('PriorityClass', wintypes.DWORD),
                ('SchedulingClass', wintypes.DWORD),
            ]

        class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ('BasicLimitInformation', JOBOBJECT_BASIC_LIMIT_INFORMATION),
                ('IoInfo', IO_COUNTERS),
                ('ProcessMemoryLimit', ctypes.c_size_t),
                ('JobMemoryLimit', ctypes.c_size_t),
                ('PeakProcessMemoryUsed', ctypes.c_size_t),
                ('PeakJobMemoryUsed', ctypes.c_size_t),
            ]

        kernel32 = ctypes.windll.kernel32
        kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        job = kernel32.CreateJobObjectW(None, None)
        if not job:
            return None

        info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.BasicLimitInformation.LimitFlags = 0x00002000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not kernel32.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info)):
            kernel32.CloseHandle(job)
            return None
        return job
    except Exception:
        return None


def assign_proc_to_job(job, proc):
    if not job or sys.platform != 'win32':
        return
    try:
        import ctypes
        ctypes.windll.kernel32.AssignProcessToJobObject(job, int(proc._handle))
    except Exception:
        pass


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
        self.cdn_port = 8080
        self.game_port = 9200
        self._job = create_windows_job_object()

    def start_services(self):
        print("==================================================================")
        print("         DDTANK LOCAL CLUSTER & EMULATOR ORCHESTRATOR             ")
        print("==================================================================")

        cleanup_stale_python_ports([843, 8080, 9200])

        self.cdn_port = find_available_port(8080)
        self.game_port = find_available_port(9200)
        if self.cdn_port != 8080:
            print(f"[!] Port 8080 occupied by another app -> switching CDN to HTTP {self.cdn_port}")
        if self.game_port != 9200:
            print(f"[!] Port 9200 occupied by another app -> switching Game Server to TCP {self.game_port}")

        ts_ip = get_tailscale_ip()
        if ts_ip:
            print(f"[+] Tailscale IP Detected: {ts_ip}")
            print(f"[+] Share this URL with your friends: http://{ts_ip}:{self.cdn_port}/player.html")
        else:
            print("[*] Tailscale not detected or offline (Running in Localhost mode)")
            print(f"[+] Local URL: http://127.0.0.1:{self.cdn_port}/player.html")

        daemon_env = os.environ.copy()
        daemon_env['DDT_CDN_PORT'] = str(self.cdn_port)
        daemon_env['DDT_GAME_PORT'] = str(self.game_port)

        # 1. Start Policy Server (TCP 843)
        print("\n[*] Starting Flash Policy Server (TCP 843)...")
        p_script = os.path.join(os.path.dirname(__file__), 'ddt_policy_server.py')
        self.procs['policy'] = subprocess.Popen([sys.executable, p_script], env=daemon_env)
        assign_proc_to_job(self._job, self.procs['policy'])

        # 2. Start CDN Asset Server (HTTP 8080 or fallback)
        print(f"[*] Starting Local Asset CDN Server (HTTP {self.cdn_port})...")
        cdn_script = os.path.join(os.path.dirname(__file__), 'ddt_local_cdn.py')
        self.procs['cdn'] = subprocess.Popen([sys.executable, cdn_script, str(self.cdn_port)], env=daemon_env)
        assign_proc_to_job(self._job, self.procs['cdn'])

        # 3. Start Game Core Server (TCP 9200 or fallback)
        print(f"[*] Starting DDTank Game Core Server (TCP {self.game_port})...")
        game_script = os.path.join(os.path.dirname(__file__), 'ddt_server.py')
        self.procs['game'] = subprocess.Popen([sys.executable, game_script, str(self.game_port)], env=daemon_env)
        assign_proc_to_job(self._job, self.procs['game'])

        cdn_ok = wait_for_port('127.0.0.1', self.cdn_port, timeout=8.0)
        game_ok = wait_for_port('127.0.0.1', self.game_port, timeout=8.0)
        if cdn_ok and game_ok:
            print("\n[+] All Daemons are Active and Ready!")
        else:
            print(f"\n[!] Warning: Port readiness check (HTTP {self.cdn_port}={cdn_ok}, TCP {self.game_port}={game_ok}).")

    def launch_client(self):
        if not os.path.exists(RUNTIME_EXE):
            print(f"[-] Runtime executable not found at {RUNTIME_EXE}")
            return
        if not os.path.exists(FLASH_DLL):
            print(f"[-] Flash Pepper plugin not found at {FLASH_DLL}")
            return

        ensure_decoupled_electron_app()

        player_url = f'http://127.0.0.1:{self.cdn_port}/player.html'
        print(f"\n[*] Launching DDTank Desktop Client ({player_url})...")
        client_env = os.environ.copy()
        client_env['DDT_SERVER_URL'] = player_url

        args = [
            RUNTIME_EXE,
            f'--ppapi-flash-path={FLASH_DLL}',
            '--ppapi-flash-version=32.0.0.371',
            player_url
        ]
        self.procs['client'] = subprocess.Popen(args, cwd=RUNTIME_DIR, env=client_env)
        assign_proc_to_job(self._job, self.procs['client'])
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
