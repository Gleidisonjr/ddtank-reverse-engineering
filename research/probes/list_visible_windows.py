import ctypes
from ctypes import wintypes
user32 = ctypes.windll.user32

def cb(hwnd, lparam):
    if user32.IsWindowVisible(hwnd):
        title = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, title, 256)
        if title.value:
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            cls = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls, 256)
            rect = wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            print(f"PID {pid.value} | HWND {hex(hwnd)} [{cls.value}] | Title: '{title.value}' | Rect: ({rect.left},{rect.top},{rect.right},{rect.bottom})")
    return True

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
user32.EnumWindows(WNDENUMPROC(cb), 0)
