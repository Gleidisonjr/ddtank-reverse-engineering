import ctypes
from ctypes import wintypes

kernel32 = ctypes.windll.kernel32
pid = 35588
hp = kernel32.OpenProcess(0x001F0FFF, False, pid)

ptr_buf = (ctypes.c_byte * 4)()
rd = ctypes.c_size_t()
kernel32.ReadProcessMemory(hp, 0x859580, ptr_buf, 4, ctypes.byref(rd))
base_ptr = int.from_bytes(bytes(ptr_buf), 'little')
print(f"base_ptr: 0x{base_ptr:08x}")

if base_ptr:
    str_buf = (ctypes.c_byte * 512)()
    kernel32.ReadProcessMemory(hp, base_ptr + 0x230, str_buf, 512, ctypes.byref(rd))
    raw = bytes(str_buf)
    try:
        s = raw.decode('utf-16le').split('\x00')[0]
        print(f"Text (UTF-16LE): '{s}'")
    except Exception as e:
        print(f"Decode err: {e}")
    try:
        s2 = raw.decode('ascii', errors='ignore').split('\x00')[0]
        print(f"Text (ASCII): '{s2}'")
    except Exception as e:
        print(f"Decode err2: {e}")
