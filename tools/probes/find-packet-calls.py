import struct

with open(r'targets\district-187\client\S2\Game\GameClient.dll', 'rb') as f:
    data = f.read()

target_va = 0x10057150
print(f"Searching for calls to 0x{target_va:08X}...")

for off in range(0x400, 0x480600 - 5):
    # check for call rel32 (0xE8)
    if data[off] == 0xE8:
        rel = struct.unpack_from('<i', data, off + 1)[0]
        cur_va = 0x10000000 + 0x1000 + (off - 0x400)
        target = cur_va + 5 + rel
        if target in [0x10057150, 0x10057157]:
            print(f"CALL at 0x{cur_va:08X} -> 0x{target:08X}")
