import ctypes
from ctypes import wintypes

kernel32 = ctypes.windll.kernel32
pid = 35588
hp = kernel32.OpenProcess(0x001F0FFF, False, pid)

buf = (ctypes.c_byte * 1024)()
rd = ctypes.c_size_t()
kernel32.ReadProcessMemory(hp, 0x001af8a4, buf, 1024, ctypes.byref(rd))
dwords = [int.from_bytes(bytes(buf)[k:k+4], 'little') for k in range(0, 1024, 4)]

for i, addr in enumerate(dwords):
    desc = ""
    if 0x400000 <= addr <= 0x860000:
        desc = f" -> TheRaw.exe + 0x{addr - 0x400000:x}"
    elif 0x10000000 <= addr <= 0x11000000:
        desc = f" -> GameClient.dll + 0x{addr - 0x10000000:x}"
    if desc or i < 16:
        print(f"  [+0x{i*4:03x}] 0x{addr:08x}{desc}")
