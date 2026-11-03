import subprocess
import time
import os
import psutil
from dump_runtime_memory import dump_process_memory

exe = os.path.abspath(r"targets\dd-classico\extracted\app\DDClassico.exe")
app_dir = os.path.dirname(exe)

env = os.environ.copy()
env["__COMPAT_LAYER"] = "RunAsInvoker"

out_dir = os.path.abspath(r"targets\dd-classico\dumped_memory")

print(f"[*] Starting {exe}...")
p = subprocess.Popen([exe], cwd=app_dir, env=env)

try:
    runtime_pids = []
    for i in range(15):
        time.sleep(0.5)
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                name = (proc.info['name'] or '').lower()
                if 'ddclassico.runtime' in name:
                    pid = proc.info['pid']
                    if pid not in runtime_pids:
                        runtime_pids.append(pid)
                        print(f"[+] Found DDClassico.Runtime.exe PID: {pid}")
            except Exception:
                pass
        if len(runtime_pids) >= 2: # Main and Renderer
            break

    print(f"[*] Targeting PIDs for memory dump: {runtime_pids}")
    for rpid in runtime_pids:
        dump_process_memory(rpid, out_dir)

finally:
    print("[*] Terminating processes...")
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if 'ddclassico' in (proc.info['name'] or '').lower():
                proc.kill()
        except Exception:
            pass
    print("[*] All processes cleaned up.")
