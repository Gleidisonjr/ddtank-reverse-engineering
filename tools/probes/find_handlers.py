import struct

with open(r'targets/district-187/client-rebirth/Game/GameClient.dll', 'rb') as f:
    dll = f.read()

for target in [0x100d74a0, 0x100d74f0, 0x100d7540, 0x100d7580]:
    pat = struct.pack('<I', target)
    idx = 0
    while True:
        p = dll.find(pat, idx)
        if p == -1: break
        # determine section
        va = None
        if p < 0x480600:
            va = 0x10001000 + (p - 0x400)
        else:
            va = 0x10482000 + (p - 0x480600)
        print(f"Target {hex(target)} found at file raw {hex(p)} (VA: {hex(va)})")
        idx = p + 1
