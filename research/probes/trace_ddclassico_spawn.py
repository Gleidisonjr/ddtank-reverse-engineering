import subprocess
import time
import os
import psutil

exe = os.path.abspath(r"targets\dd-classico\extracted\app\DDClassico.exe")
app_dir = os.path.dirname(exe)

env = os.environ.copy()
env["__COMPAT_LAYER"] = "RunAsInvoker"

print(f"[*] Launching {exe} from {app_dir}...")
p = subprocess.Popen([exe], cwd=app_dir, env=env)
print(f"[+] Started PID {p.pid}")

try:
    for i in range(10):
        time.sleep(0.5)
        procs = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'ppid']):
            try:
                info = proc.info
                name = (info['name'] or '').lower()
                if 'ddclassico' in name:
                    procs.append(info)
            except Exception:
                pass
        
        print(f"[{i*0.5:.1f}s] Active DDClassico processes ({len(procs)}):")
        for pr in procs:
            print(f"   PID: {pr['pid']}, PPID: {pr['ppid']}, Name: {pr['name']}")
            print(f"        Cmd: {pr['cmdline']}")
        
        if p.poll() is not None:
            print(f"[*] Main process exited with code {p.returncode}")
            break
finally:
    # Cleanup any spawned processes
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if 'ddclassico' in (proc.info['name'] or '').lower():
                proc.kill()
        except Exception:
            pass
