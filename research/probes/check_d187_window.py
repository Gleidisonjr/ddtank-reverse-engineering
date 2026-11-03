import ctypes
import ctypes.wintypes

user32 = ctypes.windll.user32
hdesk = user32.OpenInputDesktop(0, False, 0x01FF)
results = []

def enum_proc(hwnd, lparam):
    pid = ctypes.wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if pid.value == 16136:
        length = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        vis = user32.IsWindowVisible(hwnd)
        rect = ctypes.wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        results.append((hwnd, vis, buf.value, rect.left, rect.top, rect.right, rect.bottom))
    return 1

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)
user32.EnumDesktopWindows(hdesk, WNDENUMPROC(enum_proc), 0)

print(f"Windows found for PID 16136: {len(results)}")
for r in results:
    print(f"HWND: {hex(r[0])} | Visible: {r[1]} | Title: '{r[2]}' | Rect: ({r[3]},{r[4]})-({r[5]},{r[6]})")
