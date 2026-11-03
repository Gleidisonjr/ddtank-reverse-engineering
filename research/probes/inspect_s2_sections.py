import struct

with open(r'targets/district-187/client-rebirth/Game/GameClient.dll', 'rb') as f:
    dll = f.read()

e_lfanew = struct.unpack_from('<I', dll, 0x3c)[0]
num_sec = struct.unpack_from('<H', dll, e_lfanew+6)[0]
opt_size = struct.unpack_from('<H', dll, e_lfanew+20)[0]
sec_start = e_lfanew + 24 + opt_size

sections = {}
for i in range(num_sec):
    s = dll[sec_start + i*40 : sec_start + (i+1)*40]
    name = s[:8].rstrip(b'\x00').decode('latin1')
    va = struct.unpack_from('<I', s, 12)[0]
    raw = struct.unpack_from('<I', s, 20)[0]
    sz = struct.unpack_from('<I', s, 16)[0]
    sections[name] = (va, raw, sz)

for name in ['.s2zm', '.s2fk', '.s2mk', '.s2fp', '.s2kl']:
    va, raw, sz = sections[name]
    data = dll[raw:raw+sz]
    print(f"=== Section {name} (VA: {hex(0x10000000+va)}, Raw: {hex(raw)}, Size: {hex(sz)}) ===")
    print("Hex dump:")
    print(" ", data[:64].hex())
    # Find any ASCII strings
    import re
    strs = re.findall(rb'[a-zA-Z0-9_\-\.:/]{3,}', data)
    if strs:
        print(" Strings:", [s.decode('latin1') for s in strs])
