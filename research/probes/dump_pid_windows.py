import ctypes
from ctypes import wintypes
import sys

user32 = ctypes.windll.user32
pid = int(sys.argv[1]) if len(sys.argv) > 1 else 35588

def enum_cb(hwnd, lparam):
    p = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
    if p.value == pid:
        title = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, title, 256)
        cls = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls, 256)
        vis = user32.IsWindowVisible(hwnd)
        print(f"HWND {hex(hwnd)} [{cls.value}]: Title='{title.value}', Visible={vis}")
        def child_cb(chwnd, lparam):
            ctitle = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(chwnd, ctitle, 256)
            ccls = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(chwnd, ccls, 256)
            print(f"   Child HWND {hex(chwnd)} [{ccls.value}]: Title='{ctitle.value}'")
            return True
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        user32.EnumChildWindows(hwnd, WNDENUMPROC(child_cb), 0)
    return True

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
