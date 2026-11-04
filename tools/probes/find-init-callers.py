import struct

with open(r'targets\district-187\client\S2\Game\GameClient.dll', 'rb') as f:
    data = f.read()

# 0x1006754C is inside a function. Let's scan backwards for function prologue
off = 0x0006754C - 0x1000 + 0x400
while off > 0x400:
    # Look for push ebp; mov ebp, esp (55 8b ec) or sub esp (83 ec or 81 ec) or push esi/edi followed by sub esp
    if data[off:off+3] == b'\x55\x8b\xec' or data[off:off+2] == b'\x83\xec' or data[off:off+2] == b'\x81\xec':
        # check if preceded by ret (c3 or c2) or int3 (cc)
        if data[off-1] in [0xC3, 0xCC] or data[off-3] in [0xC2]:
            va = 0x10000000 + 0x1000 + (off - 0x400)
            print(f"Candidate function start at file offset 0x{off:06X} -> VA 0x{va:08X}")
            break
    off -= 1

func_va = va
print(f"Finding callers of 0x{func_va:08X}...")
for o in range(0x400, 0x480600 - 5):
    if data[o] == 0xE8:
        rel = struct.unpack_from('<i', data, o + 1)[0]
        cur_va = 0x10000000 + 0x1000 + (o - 0x400)
        if cur_va + 5 + rel == func_va:
            print(f"  Called from 0x{cur_va:08X}")
