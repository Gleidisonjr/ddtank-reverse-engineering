import os
import subprocess
import time
import ctypes
from ctypes import wintypes

client_dir = os.path.abspath(r'targets\district-187\client-rebirth')
raw_exe = os.path.join(client_dir, 'TheRaw.exe')

subprocess.run(['taskkill', '/F', '/IM', 'TheRaw.exe'], capture_output=True)
time.sleep(0.5)

cmd = [
    raw_exe,
    '-arch', 'game',
    '-archcfg', 'Default.archcfg',
    '-windowtitle', 'District 187: Sin Streets',
    '+gs_ip', '127.0.0.1',
    '+gs_port', '12000',
    '+windowed', '1',
    '+ScreenWidth', '1920',
    '+ScreenHeight', '1080'
]
print("Launching:", cmd)
env = os.environ.copy()
env['__COMPAT_LAYER'] = 'RunAsInvoker'
p = subprocess.Popen(cmd, cwd=client_dir, env=env)
print("PID:", p.pid)

FindWindowA = ctypes.windll.user32.FindWindowA
FindWindowA.argtypes = [wintypes.LPCSTR, wintypes.LPCSTR]
FindWindowA.restype = wintypes.HWND

found_error = False
for i in range(12):
    time.sleep(0.5)
    ret = p.poll()
    err_hwnd = FindWindowA(None, b'Error') or FindWindowA(None, b'Message Error')
    if err_hwnd:
        print(f"[{i*0.5:.1f}s] Error window detected! HWND: {err_hwnd}")
        found_error = True
        break
    main_hwnd = FindWindowA(None, b'District 187: Sin Streets')
    if main_hwnd:
        print(f"[{i*0.5:.1f}s] Game main window detected! HWND: {main_hwnd}")
    if ret is not None:
        print(f"[{i*0.5:.1f}s] Process exited with code: {ret}")
        break
    print(f"[{i*0.5:.1f}s] Still running (PID {p.pid})...")

if not found_error and p.poll() is None:
    print("SUCCESS: TheRaw.exe is running smoothly without Error pop-up!")

# Cleanup
subprocess.run(['taskkill', '/F', '/IM', 'TheRaw.exe'], capture_output=True)
