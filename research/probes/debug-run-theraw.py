import subprocess
import sys
import os

client_dir = r"C:\Users\dopamine\Desktop\Projetos\Reverse Engineering\targets\district-187\client\S2"
exe_path = os.path.join(client_dir, "TheRaw.exe")

env = os.environ.copy()
env["__COMPAT_LAYER"] = "RunAsInvoker"

args = [
    exe_path,
    "-arch", "game",
    "-windowtitle", "D187",
    "+LoginDevMode", "1",
    "+gs_ip", "127.0.0.1",
    "+gs_port", "12000",
    "+Windowed", "1",
    "+ScreenWidth", "1024",
    "+ScreenHeight", "768",
    "+ShowLog", "1",
]

print(f"[*] Running: {' '.join(args)}")
print(f"[*] Working Directory: {client_dir}")

proc = subprocess.Popen(
    args,
    cwd=client_dir,
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

try:
    stdout, stderr = proc.communicate(timeout=10)
    print(f"[*] Process exited with code: {proc.returncode} (hex {hex(proc.returncode & 0xFFFFFFFF)})")
    if stdout:
        print("[STDOUT]:", stdout.decode("latin1", errors="replace"))
    if stderr:
        print("[STDERR]:", stderr.decode("latin1", errors="replace"))
except subprocess.TimeoutExpired:
    print("[*] Process is still running after 10s!")
    proc.terminate()
