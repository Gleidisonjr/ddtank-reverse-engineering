import struct, capstone

with open(r'targets/district-187/client-rebirth/Game/GameClient.dll', 'rb') as f:
    dll = f.read()

pos = dll.find(b'CNetworkSendPacketMgr')
while pos != -1:
    va = 0x10482000 + (pos - 0x480600)
    print("Found CNetworkSendPacketMgr at raw:", hex(pos), "VA:", hex(va))
    pat = struct.pack('<I', va)
    idx = 0
    while True:
        p = dll.find(pat, idx)
        if p == -1: break
        rva = 0x10001000 + (p - 0x400) if p < 0x480600 else 0x10482000 + (p - 0x480600)
        print(f"  Referenced at VA: {hex(rva)}")
        idx = p + 1
    pos = dll.find(b'CNetworkSendPacketMgr', pos + 1)
