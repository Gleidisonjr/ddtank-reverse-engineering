import zlib
import struct

with open('projects/ddtank-server/www/flash/Loading.swf', 'rb') as f:
    data = f.read()

body = zlib.decompress(data[8:])

p = 0
nbits = body[0] >> 3
nbits_bytes = (5 + nbits * 4 + 7) // 8
p += nbits_bytes + 4

while p < len(body) - 2:
    tag_code_len = struct.unpack('<H', body[p:p+2])[0]
    p += 2
    code = tag_code_len >> 6
    length = tag_code_len & 0x3F
    if length == 0x3F:
        length = struct.unpack('<I', body[p:p+4])[0]
        p += 4
    if code in (82, 72):
        name_end = body.find(b'\x00', p+4)
        abc_data = body[name_end+1:p+length]
        break
    p += length

def read_u30(buf, idx):
    res = 0; shift = 0
    while True:
        b = buf[idx]; idx += 1
        res |= (b & 0x7F) << shift
        if not (b & 0x80): break
        shift += 7
    return res, idx

pos = 4
int_count, pos = read_u30(abc_data, pos)
for _ in range(1, int_count): _, pos = read_u30(abc_data, pos)
uint_count, pos = read_u30(abc_data, pos)
for _ in range(1, uint_count): _, pos = read_u30(abc_data, pos)
double_count, pos = read_u30(abc_data, pos)
if double_count > 0: pos += (double_count - 1) * 8

string_count, pos = read_u30(abc_data, pos)
strings = ['']
for _ in range(1, string_count):
    slen, pos = read_u30(abc_data, pos)
    s = abc_data[pos:pos+slen].decode('utf-8', errors='ignore')
    pos += slen
    strings.append(s)

print(f"Block 0 string count: {len(strings)}")
for i, s in enumerate(strings):
    print(f"  {i:3d}: {s}")
