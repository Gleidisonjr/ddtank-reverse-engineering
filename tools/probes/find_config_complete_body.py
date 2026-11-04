import zlib
import struct

with open('projects/ddtank-server/www/flash/Loading.swf', 'rb') as f:
    data = f.read()

body = zlib.decompress(data[8:])

# Let's search in the first DoABC block for __onConfigLoadComplete
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
        abc = body[p:p+length]
        break
    p += length

name_end = abc.find(b'\x00', 4)
abc_data = abc[name_end+1:]

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

# Let's find the string table
pos = 4
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
strings = ['']
for _ in range(1, string_count):
    slen, pos = read_u30(abc_data, pos)
    s = abc_data[pos:pos+slen].decode('utf-8', errors='ignore')
    pos += slen
    strings.append(s)

target_idx = strings.index('__onConfigLoadComplete')
print(f"'__onConfigLoadComplete' string index: {target_idx}")

# Search for where target_idx appears as a method trait in ABC
# Let's search method bodies
# Since method bodies are at the end, let's look for method bodies that reference 'LoginSelectList.ashx' or 'FLASHSITE'
login_idx = strings.index('LoginSelectList.ashx')
print(f"'LoginSelectList.ashx' string index: {login_idx}")
flashsite_idx = strings.index('FLASHSITE')
print(f"'FLASHSITE' string index: {flashsite_idx}")

# Find occurrences of 0x2C (pushstring) followed by flashsite_idx or login_idx
for name, sidx in [('FLASHSITE', flashsite_idx), ('LoginSelectList.ashx', login_idx)]:
    needle = bytes([0x2C, sidx]) if sidx < 128 else bytes([0x2C, (sidx & 0x7F) | 0x80, sidx >> 7])
    for i in range(len(abc_data)):
        if abc_data[i:i+len(needle)] == needle:
            print(f"Found pushstring '{name}' at offset {i}")
            # print 120 bytes of instructions starting at i-10
            snippet = abc_data[max(0, i-10):i+150]
            print("Hex:", snippet.hex())
