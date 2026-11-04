from find_hashead_idx import abc_data, read_u30
from decompile_loading_all import disasm

# mn 885 in u30 is:
# 885 = (885 & 0x7F) | 0x80, 885 >> 7 = 0xF5, 0x06
needle = bytes([0xF5, 0x06])
pos = 0
while True:
    pos = abc_data.find(needle, pos)
    if pos == -1: break
    print(f"mn 885 at {pos}")
    # let's inspect 100 bytes around pos
    chunk = abc_data[max(0, pos-20):pos+80]
    print("   ", chunk.hex())
    pos += 1
