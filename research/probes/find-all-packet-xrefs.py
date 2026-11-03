import struct

with open(r'targets\district-187\client\S2\Game\GameClient.dll', 'rb') as f:
    data = f.read()

for name, va in [('SA_JoyGameLogin', 0x1048C0C4), ('SA_Login', 0x1048C11C), ('CQ_JoyGameLogin', 0x1048C0F0)]:
    print(f"Xrefs for {name} (0x{va:08X}):")
    for off in range(0x400, len(data) - 4):
        val = struct.unpack_from('<I', data, off)[0]
        if val == va:
            rva = 0x1000 + (off - 0x400) if off < 0x480600 else 0x482000 + (off - 0x480600)
            cva = 0x10000000 + rva
            print(f"  Offset 0x{off:06X} -> VA 0x{cva:08X}")
