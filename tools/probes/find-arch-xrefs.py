import struct

with open(r'targets\district-187\client\S2\TheRaw.exe', 'rb') as f:
    data = f.read()

# file offset 0x3DB608 -> VA
# in TheRaw.exe, .rdata raw offset 0x3DA600, VA 0x007DB000
# 0x3DB608 - 0x3DA600 + 0x007DB000 = 0x007DC008
str_va = 0x007DC008

print("Searching for -arch xrefs...")
for off in range(0x400, 0x3DA600 - 4):
    val = struct.unpack_from('<I', data, off)[0]
    if val == str_va:
        code_va = 0x400000 + 0x1000 + (off - 0x400)
        print(f"Xref at offset 0x{off:06X} -> VA 0x{code_va:08X}")
