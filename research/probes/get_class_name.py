import struct

with open(r'targets/district-187/client-rebirth/Game/GameClient.dll', 'rb') as f:
    dll = f.read()

def va2raw(va):
    return 0x480600 + (va - 0x10482000)

col_va = struct.unpack_from('<I', dll, va2raw(0x1049df58) - 4)[0]
print(f"RTTI Complete Object Locator: {hex(col_va)}")
td_rva = struct.unpack_from('<I', dll, va2raw(col_va) + 12)[0]
td_va = 0x10000000 + td_rva
print(f"Type Descriptor: {hex(td_va)}")
td_raw = va2raw(td_va) if td_va >= 0x10482000 else 0x400 + (td_va - 0x10001000)
# In .data or .rdata
print("Class name:", dll[td_raw+8:td_raw+80].split(b'\x00')[0].decode('latin1', errors='ignore'))
