import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

def check_pid(target_pid):
    found = []
    def callback(hwnd, lparam):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == target_pid:
            length = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            cls_buf = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls_buf, 256)
            visible = user32.IsWindowVisible(hwnd)
            found.append((hwnd, buf.value, cls_buf.value, visible))
        return True

    user32.EnumWindows(WNDENUMPROC(callback), 0)
    for h, title, cls, vis in found:
        print(f"HWND {hex(h)}: Title='{title}', Class='{cls}', Visible={vis}")

if __name__ == "__main__":
    import sys
    pid = int(sys.argv[1]) if len(sys.argv) > 1 else 23716
    check_pid(pid)
