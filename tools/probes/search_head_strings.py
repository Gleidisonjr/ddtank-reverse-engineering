from find_hashead_idx import abc_data, read_u30
from decompile_loading_all import disasm

# Let's search for method bodies that call 'readUTFBytes' or 'readByte' in abc_data
for s in [b'road7', b'swf_head', b'readUTFBytes', b'position']:
    idx = 0
    while True:
        idx = abc_data.find(s, idx)
        if idx == -1: break
        print(f"String '{s.decode()}' at {idx}")
        idx += 1
