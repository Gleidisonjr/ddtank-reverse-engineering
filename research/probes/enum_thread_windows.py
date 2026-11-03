import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

tids = [26632, 19748, 4388, 31488, 13472, 35500, 32352, 16056, 32056, 31688, 22992, 32180, 3712]

def thread_wnd_cb(hwnd, lparam):
    title = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(hwnd, title, 256)
    cls = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, cls, 256)
    vis = user32.IsWindowVisible(hwnd)
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    print(f"HWND {hex(hwnd)} on TID {lparam}: Class='{cls.value}', Title='{title.value}', Vis={vis}, Rect=({rect.left},{rect.top},{rect.right},{rect.bottom})")
    return True

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

for tid in tids:
    user32.EnumThreadWindows(tid, WNDENUMPROC(thread_wnd_cb), tid)
print("Done EnumThreadWindows.")
