from find_hashead_idx import abc_data, read_u30
from find_hashead_mn import hashead_mn_indices

# Let's search for opcode 0x4f / 0x46 / 0x66 with mn in hashead_mn_indices
for mn in hashead_mn_indices:
    # u30 representation of mn
    b = []
    v = mn
    while True:
        byte = v & 0x7F
        v >>= 7
        if v:
            b.append(byte | 0x80)
        else:
            b.append(byte)
            break
    needle = bytes(b)
    # Search in abc_data
    pos = 0
    while True:
        pos = abc_data.find(needle, pos)
        if pos == -1: break
        # check preceding opcode
        if pos > 0:
            op = abc_data[pos-1]
            if op in (0x4f, 0x46, 0x66, 0x60):
                print(f"Call/get of hasHead (mn {mn}) at offset {pos-1}: op=0x{op:02x}")
                # print 60 bytes around pos
                chunk = abc_data[pos-1:pos+60]
                print(f"   Hex: {chunk.hex()}")
        pos += 1
