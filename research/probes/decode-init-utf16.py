with open(r'targets\district-187\client\S2\Game\GameClient.dll', 'rb') as f:
    data = f.read()

for addr in [0x104ab940, 0x104ab8e0, 0x104ab878, 0x104ab808]:
    off = addr - 0x10000000 - 0x00482000 + 0x00480600
    chunk = data[off : off + 200]
    end = chunk.find(b'\x00\x00\x00')
    if end != -1: chunk = chunk[:end+1]
    decoded = chunk.decode("utf-16le", errors="ignore")
    print(f"0x{addr:08X}: \"{decoded}\"")
