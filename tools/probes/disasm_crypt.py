import struct

with open(r'targets/district-187/client-rebirth/Game/GameClient.dll', 'rb') as f:
    dll = f.read()

off = 0x668c2
print("Bytes around 0x668c2:")
print(dll[off-30:off+60].hex())

# Let's inspect all strings nearby in .rdata
print("Strings nearby in .rdata:")
for s in dll[0x48d600:0x48d800].split(b'\x00'):
    if s: print(' ', s.decode('latin1', errors='ignore'))
