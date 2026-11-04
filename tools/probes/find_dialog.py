import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

pid = 18536
tid = 25224

WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

found = []

def enum_cb(hwnd, lparam):
    w_pid = wintypes.DWORD()
    w_tid = user32.GetWindowThreadProcessId(hwnd, ctypes.byref(w_pid))
    if w_pid.value == pid:
        title = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, title, 512)
        cls = ctypes.create_unicode_buffer(512)
        user32.GetClassNameW(hwnd, cls, 512)
        visible = user32.IsWindowVisible(hwnd)
        print(f'HWND=0x{hwnd:08x}, Visible={visible}, Class="{cls.value}", Title="{title.value}"')
        found.append(hwnd)
        
        def child_cb(chwnd, clparam):
            ctitle = ctypes.create_unicode_buffer(512)
            user32.GetWindowTextW(chwnd, ctitle, 512)
            ccls = ctypes.create_unicode_buffer(512)
            user32.GetClassNameW(chwnd, ccls, 512)
            print(f'   Child 0x{chwnd:08x}: Class="{ccls.value}", Text="{ctitle.value}"')
            return True
            
        user32.EnumChildWindows(hwnd, WNDENUMPROC(child_cb), 0)
    return True

print(f"Enumerating windows for PID {pid}...")
user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
user32.EnumThreadWindows(tid, WNDENUMPROC(enum_cb), 0)
print(f"Done. Found {len(found)} windows.")
