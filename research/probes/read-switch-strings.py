with open(r'targets\district-187\client\S2\Game\GameClient.dll', 'rb') as f:
    data = f.read()

for addr in [0x10489590, 0x1048956c, 0x10489548, 0x10489524, 0x10489504, 0x104894e0]:
    off = addr - 0x10000000 - 0x00482000 + 0x00480600
    s = ''
    while off < len(data) and data[off] != 0:
        s += chr(data[off])
        off += 1
    print(f"0x{addr:08X}: \"{s}\"")
