import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

def inspect_dialog():
    found_hwnds = []
    def enum_cb(hwnd, lparam):
        title = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, title, 256)
        if title.value == 'Error':
            found_hwnds.append(hwnd)
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows(WNDENUMPROC(enum_cb), 0)

    for h in found_hwnds:
        print(f"Dialog HWND: {hex(h)}")
        def child_cb(chwnd, lparam):
            txt = ctypes.create_unicode_buffer(512)
            user32.GetWindowTextW(chwnd, txt, 512)
            cls = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(chwnd, cls, 256)
            print(f"   Child {hex(chwnd)} [{cls.value}]: '{txt.value}'")
            return True
        user32.EnumChildWindows(h, WNDENUMPROC(child_cb), 0)

if __name__ == "__main__":
    inspect_dialog()
