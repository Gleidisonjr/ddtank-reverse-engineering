import subprocess
import time
import os
import glob
import psutil

exe = os.path.abspath(r"targets\dd-classico\extracted\app\DDClassico.exe")
app_dir = os.path.dirname(exe)

env = os.environ.copy()
env["__COMPAT_LAYER"] = "RunAsInvoker"

print(f"[*] Launching {exe}...")
p = subprocess.Popen([exe], cwd=app_dir, env=env)
time.sleep(2.0)

try:
    print(f"[+] DDClassico.exe running with PID {p.pid}")
    
    # 1. Enumerate all child processes
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'ppid']):
        try:
            if 'ddclassico' in (proc.info['name'] or '').lower():
                print(f"Proc: PID={proc.info['pid']}, Name={proc.info['name']}")
                print(f"      Cmd={proc.info['cmdline']}")
        except Exception:
            pass

    # 2. Check Named Pipes
    pipes = glob.glob(r'\\.\pipe\*')
    print(f"[+] Total pipes open on system: {len(pipes)}")
    for pipe in pipes:
        plow = pipe.lower()
        if any(k in plow for k in ['dd', 'classico', '4431', 'electron']):
            print(f"   Pipe: {pipe}")

    # 3. Check TCP/UDP connections of DDClassico processes
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if 'ddclassico' in (proc.info['name'] or '').lower():
                conns = proc.connections()
                if conns:
                    print(f"[+] Network connections for {proc.info['name']} (PID {proc.info['pid']}):")
                    for c in conns:
                        print(f"      {c.type} {c.laddr} -> {c.raddr} ({c.status})")
        except Exception:
            pass

finally:
    print("[*] Terminating test processes...")
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if 'ddclassico' in (proc.info['name'] or '').lower():
                proc.kill()
        except Exception:
            pass
