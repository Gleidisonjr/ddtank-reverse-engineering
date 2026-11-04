import struct

with open('projects/ddtank-server/www/flash/1.swf', 'rb') as f:
    raw = f.read()

# Let's find DoABC
body = raw[8:]
p = 0
nbits = body[0] >> 3
p += (5 + nbits * 4 + 7) // 8 + 4

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
        abc = tag_data
        break

name_end = abc.find(b'\x00', 4)
abc_data = abc[name_end+1:]

# Let's search for string 'hasHead' in abc_data
pos = abc_data.find(b'hasHead')
print('hasHead in abc_data at', pos)

# Let's search for the method body referencing hasHead
# In multinames, hasHead has a specific index
# Let's search where the method is defined
def read_u30(buf, idx):
    res = 0; shift = 0
    while True:
        b = buf[idx]; idx += 1
        res |= (b & 0x7F) << shift
        if not (b & 0x80): break
        shift += 7
    return res, idx

# Scan all string constants
p = 4
int_count, p = read_u30(abc_data, p)
for _ in range(1, int_count): _, p = read_u30(abc_data, p)
uint_count, p = read_u30(abc_data, p)
for _ in range(1, uint_count): _, p = read_u30(abc_data, p)
double_count, p = read_u30(abc_data, p)
if double_count > 0: p += (double_count - 1) * 8

string_count, p = read_u30(abc_data, p)
strings = ['']
hashead_str_idx = None
for sidx in range(1, string_count):
    slen, p = read_u30(abc_data, p)
    s = abc_data[p:p+slen].decode('utf-8', errors='ignore')
    p += slen
    strings.append(s)
    if s == 'hasHead':
        hashead_str_idx = sidx

print(f"hasHead string index: {hashead_str_idx}")
