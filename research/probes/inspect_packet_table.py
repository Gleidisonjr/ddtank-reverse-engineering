import struct

with open(r'targets/district-187/client-rebirth/Game/GameClient.dll', 'rb') as f:
    dll = f.read()

# .rdata is VA 0x10482000, raw 0x480600
def va2raw(va):
    return 0x480600 + (va - 0x10482000)

raw = va2raw(0x1049d158)
print("=== Packet Table around 0x1049d158 ===")
for i in range(-5, 10):
    val = struct.unpack_from('<I', dll, raw + i*8)[0]
    handler = struct.unpack_from('<I', dll, raw + i*8 + 4)[0]
    print(f"  [{i}] ID: {hex(val)} -> Handler: {hex(handler)}")
