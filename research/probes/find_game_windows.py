import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

def enum_cb(hwnd, lparam):
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    title = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(hwnd, title, 256)
    if 'District' in title.value or 'Error' in title.value or 'TheRaw' in title.value:
        cls = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls, 256)
        vis = user32.IsWindowVisible(hwnd)
        print(f"HWND {hex(hwnd)} [PID {pid.value}] [{cls.value}]: Title='{title.value}', Visible={vis}")
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
