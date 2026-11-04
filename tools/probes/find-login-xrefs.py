import struct
import capstone

with open(r'targets\district-187\client\S2\Game\GameClient.dll', 'rb') as f:
    data = f.read()

cq_login_va = 0x1048C140
sa_login_va = 0x1048C11C

print("--- Searching for CQ_Login (0x1048C140) xrefs ---")
for off in range(0x400, len(data) - 4):
    val = struct.unpack_from('<I', data, off)[0]
    if val == cq_login_va:
        rva = 0x1000 + (off - 0x400) if off < 0x480600 else 0x482000 + (off - 0x480600)
        va = 0x10000000 + rva
        print(f"Xref at offset 0x{off:06X} -> VA 0x{va:08X}")

print("--- Searching for SA_Login (0x1048C11C) xrefs ---")
for off in range(0x400, len(data) - 4):
    val = struct.unpack_from('<I', data, off)[0]
    if val == sa_login_va:
        rva = 0x1000 + (off - 0x400) if off < 0x480600 else 0x482000 + (off - 0x480600)
        va = 0x10000000 + rva
        print(f"Xref at offset 0x{off:06X} -> VA 0x{va:08X}")
