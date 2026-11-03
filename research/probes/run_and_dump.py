import subprocess
import time
import os
import psutil

exe = os.path.abspath(r"targets\dd-classico\extracted\app\DDClassico.exe")
app_dir = os.path.dirname(exe)

env = os.environ.copy()
env["__COMPAT_LAYER"] = "RunAsInvoker"

dump_dir = os.path.abspath(r"targets\dd-classico\dumped_code")
print(f"[*] Launching {exe} with hook active...")
p = subprocess.Popen([exe], cwd=app_dir, env=env)

for i in range(12):
    time.sleep(0.5)
    if os.path.exists(dump_dir):
        files = os.listdir(dump_dir)
        if files:
            print(f"[{i*0.5:.1f}s] Dumped files detected ({len(files)}): {files}")

# Cleanup
for proc in psutil.process_iter(['pid', 'name']):
    try:
        if 'ddclassico' in (proc.info['name'] or '').lower():
            proc.kill()
    except Exception:
        pass

print("[*] Test run complete.")
if os.path.exists(dump_dir):
    print("[+] Final dumped directory contents:")
    for fn in os.listdir(dump_dir):
        fp = os.path.join(dump_dir, fn)
        print(f"   {fn:<25} ({os.path.getsize(fp)} bytes)")
