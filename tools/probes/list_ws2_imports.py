import struct

with open(r'targets/district-187/client-rebirth/Game/GameClient.dll', 'rb') as f:
    dll = f.read()

# Let's inspect all imports from WS2_32.dll
import re
pos = 0x482528 # IAT RVA
# Let's find section containing 0x482528
# .rdata is VA 0x10482000, raw 0x480600
raw_iat = 0x480600 + (0x482528 - 0x482000)

for i in range(50):
    val = struct.unpack_from('<I', dll, raw_iat + i*4)[0]
    if val == 0: break
    if val & 0x80000000:
        print(f"  Ordinal: {val & 0xffff}")
    else:
        # RVA
        rva = val
        raw_name = 0x480600 + (rva - 0x482000)
        if 0 <= raw_name < len(dll):
            hint = struct.unpack_from('<H', dll, raw_name)[0]
            name = dll[raw_name+2:dll.find(b'\x00', raw_name+2)].decode('latin1', errors='ignore')
            print(f"  [{i}] Hint: {hint}, Name: {name}, IAT VA: {hex(0x10482528 + i*4)}")
