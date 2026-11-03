import struct

with open(r'targets\district-187\client\S2\Game\GameClient.dll', 'rb') as f:
    data = f.read()

# 0x0565B6 is file offset
start_off = 0x056500
for off in range(start_off, start_off + 0x150, 16):
    rva = 0x1000 + (off - 0x400)
    va = 0x10000000 + rva
    dwords = struct.unpack_from('<IIII', data, off)
    print(f"0x{va:08X} (off 0x{off:06X}): {dwords[0]:08X} {dwords[1]:08X} {dwords[2]:08X} {dwords[3]:08X}")
