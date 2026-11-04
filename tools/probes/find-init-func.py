import struct

with open(r'targets\district-187\client\S2\Game\GameClient.dll', 'rb') as f:
    data = f.read()

# file offset 0x48BC40 -> VA:
# 0x48BC40 - 0x480600 + 0x00482000 = 0x0048D640
# VA = 0x1048D640
str_va = 0x1048D640

for off in range(0x400, 0x480600 - 4):
    val = struct.unpack_from('<I', data, off)[0]
    if val == str_va:
        code_rva = 0x1000 + (off - 0x400)
        code_va = 0x10000000 + code_rva
        print(f"Xref at offset 0x{off:06X} -> VA 0x{code_va:08X}")
