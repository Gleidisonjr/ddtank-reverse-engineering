import os
import subprocess
import time
import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

def test_launch():
    subprocess.run(["taskkill", "/f", "/im", "TheRaw.exe"], capture_output=True)
    time.sleep(1)

    client_dir = os.path.abspath(r"targets\district-187\client-rebirth")
    cmd = [
        os.path.join(client_dir, "TheRaw.exe"),
        "-arch", "game",
        "-archcfg", "Default.archcfg",
        "-windowtitle", "District 187: Sin Streets",
        "+gs_ip", "127.0.0.1",
        "+gs_port", "12000",
        "+windowed", "1",
        "+ScreenWidth", "1920",
        "+ScreenHeight", "1080"
    ]

    env = os.environ.copy()
    env["__COMPAT_LAYER"] = "RunAsInvoker"

    print(f"[*] Starting process from {client_dir}...")
    p = subprocess.Popen(
        cmd,
        cwd=client_dir,
        env=env
    )
    print(f"[+] Started PID {p.pid}")

    for i in range(20):
        time.sleep(0.5)
        ret = p.poll()
        if ret is not None:
            print(f"[!] Process exited prematurely with return code {ret}")
            return False

        found = []
        def enum_cb(hwnd, lparam):
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value == p.pid:
                title = ctypes.create_unicode_buffer(256)
                user32.GetWindowTextW(hwnd, title, 256)
                cls = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, cls, 256)
                vis = user32.IsWindowVisible(hwnd)
                rect = wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(rect))
                found.append((hwnd, title.value, cls.value, vis, (rect.left, rect.top, rect.right, rect.bottom)))
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(WNDENUMPROC(enum_cb), 0)

        if found:
            print(f"[{i*0.5:.1f}s] Windows found for PID {p.pid}:")
            has_game = False
            for hwnd, title, cls, vis, rect in found:
                print(f"   HWND: {hex(hwnd)} [{cls}], Title: '{title}', Visible: {vis}, Rect: {rect}")
                if "District" in title and vis:
                    has_game = True
            if has_game:
                print("[SUCCESS] Game window is visible and running!")
                return True

    return True

if __name__ == "__main__":
    test_launch()
