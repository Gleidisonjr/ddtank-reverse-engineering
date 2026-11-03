import ctypes
from ctypes import wintypes
import sys

user32 = ctypes.windll.user32
target_pid = int(sys.argv[1]) if len(sys.argv) > 1 else 7748

def enum_callback(hwnd, extra):
    length = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    visible = bool(user32.IsWindowVisible(hwnd))
    class_buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, class_buf, 256)
    rect = (wintypes.LONG * 4)()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    print(f"HWND: 0x{hwnd:x}, Class: '{class_buf.value}', Title: '{buf.value}', Visible: {visible}, Rect: ({rect[0]},{rect[1]})-({rect[2]},{rect[3]})")
    return True

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

# Check all threads via Toolhelp32Snapshot
TH32CS_SNAPTHREAD = 0x00000004
class THREADENTRY32(ctypes.Structure):
    _fields_ = [
        ('dwSize', wintypes.DWORD),
        ('cntUsage', wintypes.DWORD),
        ('th32ThreadID', wintypes.DWORD),
        ('th32OwnerProcessID', wintypes.DWORD),
        ('tpBasePri', wintypes.LONG),
        ('tpDeltaPri', wintypes.LONG),
        ('dwFlags', wintypes.DWORD),
    ]

kernel32 = ctypes.windll.kernel32
h_snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0)
te = THREADENTRY32()
te.dwSize = ctypes.sizeof(te)
if kernel32.Thread32First(h_snap, ctypes.byref(te)):
    while True:
        if te.th32OwnerProcessID == target_pid:
            user32.EnumThreadWindows(te.th32ThreadID, WNDENUMPROC(enum_callback), 0)
        if not kernel32.Thread32Next(h_snap, ctypes.byref(te)):
            break
kernel32.CloseHandle(h_snap)
