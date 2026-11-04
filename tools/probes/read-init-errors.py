with open(r'targets\district-187\client\S2\Game\GameClient.dll', 'rb') as f:
    data = f.read()

def read_str(va):
    off = va - 0x10000000 - 0x00482000 + 0x00480600
    s = ''
    while off < len(data) and data[off] != 0:
        s += chr(data[off])
        off += 1
    return s

for addr in [0x104ab940, 0x104ab8e0, 0x104ab878, 0x104ab808]:
    print(f"0x{addr:08X}: \"{read_str(addr)}\"")
