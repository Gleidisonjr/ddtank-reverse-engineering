import zlib
import struct

with open('projects/ddtank-server/www/flash/Loading.swf', 'rb') as f:
    data = f.read()

body = zlib.decompress(data[8:])

# Find DoABC tags in Loading.swf
p = 0
# Skip SWF header: rect, frame rate (2), frame count (2)
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
    if code in (82, 72): # DoABC
        abc_blocks.append(tag_data)

print(f"Found {len(abc_blocks)} DoABC blocks in Loading.swf")

# Search inside the DoABC block for method names and strings
abc = abc_blocks[0]
flags = struct.unpack('<I', abc[:4])[0]
# abc name
name_end = abc.find(b'\x00', 4)
abc_name = abc[4:name_end].decode('ascii', errors='ignore')
print(f"ABC Name: {abc_name}")
abc_data = abc[name_end+1:]

# Print strings from string pool
# In ABC: minor_version (u16), major_version (u16), cpool_info:
# u30 int_count, u30 uint_count, u30 double_count, u30 string_count
pos = 4
def read_u30(buf, idx):
    res = 0
    shift = 0
    while True:
        b = buf[idx]
        idx += 1
        res |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return res, idx

int_count, pos = read_u30(abc_data, pos)
for _ in range(1, int_count):
    _, pos = read_u30(abc_data, pos)

uint_count, pos = read_u30(abc_data, pos)
for _ in range(1, uint_count):
    _, pos = read_u30(abc_data, pos)

double_count, pos = read_u30(abc_data, pos)
if double_count > 0:
    pos += (double_count - 1) * 8

string_count, pos = read_u30(abc_data, pos)
print(f"String count: {string_count}")

strings = ['']
for _ in range(1, string_count):
    slen, pos = read_u30(abc_data, pos)
    s = abc_data[pos:pos+slen].decode('utf-8', errors='ignore')
    pos += slen
    strings.append(s)

for s in strings:
    if any(k in s.lower() for k in ['login', 'select', 'config', 'load', 'request']):
        print("  ABC String:", s)
