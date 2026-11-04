import struct

with open(r'targets/district-187/client-rebirth/Game/GameClient.dll', 'rb') as f:
    dll = f.read()

# raw 0x49c558
raw = 0x49c558
for i in range(-4, 15):
    entry_raw = raw + i*12 # or let's inspect 4-byte words
    words = [struct.unpack_from('<I', dll, raw + i*16 + j*4)[0] for j in range(4)]
    print(f"[{i:2d}] " + " ".join(f"{w:08x}" for w in words))
