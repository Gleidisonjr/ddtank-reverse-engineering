import zlib
import struct

with open('projects/ddtank-server/www/flash/Loading.swf', 'rb') as f:
    data = f.read()

body = zlib.decompress(data[8:])

p = 0
nbits = body[0] >> 3
nbits_bytes = (5 + nbits * 4 + 7) // 8
p += nbits_bytes + 4

abc_blocks = []
while p < len(body) - 2:
    tag_code_len = struct.unpack('<H', body[p:p+2])[0]
    p += 2
    code = tag_code_len >> 6
    length = tag_code_len & 0x3F
    if length == 0x3F:
        length = struct.unpack('<I', body[p:p+4])[0]
        p += 4
    tag_data = body[p:p+length]
    p += length
    if code in (82, 72):
        name_end = tag_data.find(b'\x00', 4)
        name = tag_data[4:name_end].decode('ascii', errors='ignore')
        abc_blocks.append((name, tag_data[name_end+1:]))

print(f"Total ABC blocks: {len(abc_blocks)}")
for i, (name, abc_data) in enumerate(abc_blocks):
    print(f"Block {i}: {name} (len={len(abc_data)})")
