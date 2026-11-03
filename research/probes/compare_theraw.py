import struct

with open(r'targets/district-187/client/S2/TheRaw.exe', 'rb') as f:
    old_data = f.read()

with open(r'targets/district-187/client-rebirth/TheRaw.exe', 'rb') as f:
    new_data = f.read()

print(f"Old size: {len(old_data)}, New size: {len(new_data)}")

# Compare differences
diffs = []
for i in range(min(len(old_data), len(new_data))):
    if old_data[i] != new_data[i]:
        diffs.append(i)

print(f"Total byte differences: {len(diffs)}")
if diffs:
    print(f"First diff at offset: hex {hex(diffs[0])}")
    # Group contiguous diff blocks
    blocks = []
    start = diffs[0]
    prev = diffs[0]
    for d in diffs[1:]:
        if d == prev + 1:
            prev = d
        else:
            blocks.append((start, prev - start + 1))
            start = d
            prev = d
    blocks.append((start, prev - start + 1))
    print(f"Diff blocks: {len(blocks)}")
    for b_off, b_len in blocks[:10]:
        print(f"  Offset {hex(b_off)} ({b_len} bytes):")
        print(f"    Old: {old_data[b_off:b_off+min(16, b_len)].hex()}")
        print(f"    New: {new_data[b_off:b_off+min(16, b_len)].hex()}")
