with open(r'targets/district-187/client-rebirth/Game/GameClient.dll', 'rb') as f:
    dll = f.read()

def va2raw(va):
    return 0x480600 + (va - 0x10482000)

vas = [0x1048c1c8, 0x1048c198, 0x1048c164, 0x1048c140, 0x1048c11c, 0x1048c0f0, 0x1048c0c4, 0x1048c09c, 0x1048c074, 0x1048c050, 0x1048c02c, 0x1048c008]
for va in vas:
    raw = va2raw(va)
    end = dll.find(b'\x00', raw)
    print(f"VA 0x{va:x}: {dll[raw:end].decode('latin1')}")
