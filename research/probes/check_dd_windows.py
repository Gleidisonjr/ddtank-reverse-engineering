import subprocess
import time
import os
import psutil
import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

exe = os.path.abspath(r"targets\dd-classico\extracted\app\DDClassico.exe")
app_dir = os.path.dirname(exe)

env = os.environ.copy()
env["__COMPAT_LAYER"] = "RunAsInvoker"

print(f"[*] Launching {exe}...")
p = subprocess.Popen([exe], cwd=app_dir, env=env)
time.sleep(4.0)

try:
    print("[*] Enumerating top-level windows...")
    windows = []
    def enum_cb(hwnd, lparam):
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value
            cls_buf = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls_buf, 256)
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if any(k in title.lower() or k in cls_buf.value.lower() for k in ['dd', 'classico', 'chrome', 'electron']) or pid.value in [p.pid]:
                windows.append((hwnd, pid.value, cls_buf.value, title, user32.IsWindowVisible(hwnd)))
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows(WNDENUMPROC(enum_cb), 0)

    for hwnd, pid, cls, title, vis in windows:
        print(f"HWND: 0x{hwnd:x} | PID: {pid} | Class: {cls} | Visible: {vis} | Title: '{title}'")

finally:
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if 'ddclassico' in (proc.info['name'] or '').lower():
                proc.kill()
        except Exception:
            pass
