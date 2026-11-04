import re

with open(r'targets\district-187\client\S2\Game\GameClient.dll', 'rb') as f:
    data = f.read()

matches = re.finditer(rb'tPacket_[a-zA-Z0-9_]+', data)
packets = {}
for m in matches:
    name = m.group(0).decode('latin1')
    off = m.start()
    rva = 0x482000 + (off - 0x480600)
    va = 0x10000000 + rva
    packets[name] = (off, va)

print(f"Total tPacket_ names found: {len(packets)}")
for name, (off, va) in sorted(packets.items())[:100]:
    print(f"0x{va:08X} (offset 0x{off:06X}): {name}")
