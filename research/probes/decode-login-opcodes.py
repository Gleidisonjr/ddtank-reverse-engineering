import struct

with open(r'targets\district-187\client\S2\Game\GameClient.dll', 'rb') as f:
    data = f.read()

# Table addresses:
# index_table: 0x100584c8
# jump_table: 0x10058498

def va_to_off(va):
    if va < 0x10001000: return None
    rva = va - 0x10000000
    if rva < 0x00480000:
        return 0x400 + (rva - 0x1000)
    else:
        return 0x480600 + (rva - 0x00482000)

idx_tab_off = va_to_off(0x100584c8)
jmp_tab_off = va_to_off(0x10058498)

print(f"idx_tab_off: 0x{idx_tab_off:06X}, jmp_tab_off: 0x{jmp_tab_off:06X}")

# Map of push handlers:
# At each jump target, read the pushed string
for delta in range(0x52):
    idx = data[idx_tab_off + delta]
    target_va = struct.unpack_from('<I', data, jmp_tab_off + idx * 4)[0]
    target_off = va_to_off(target_va)
    # Target code usually does push 0x1048xxxx; jmp 0x10058450
    push_val = struct.unpack_from('<I', data, target_off + 1)[0]
    str_off = va_to_off(push_val)
    s = ''
    while str_off and str_off < len(data) and data[str_off] != 0:
        s += chr(data[str_off])
        str_off += 1
    opcode = 0x110101 + delta
    print(f"Opcode 0x{opcode:06X} (delta {delta:02X}): target 0x{target_va:08X} -> {s}")
