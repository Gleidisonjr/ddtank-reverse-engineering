import struct

with open('projects/ddtank-server/www/flash/2.swf', 'rb') as f:
    raw = f.read()

p = 0
nbits = raw[8] >> 3
p = 8 + (5 + nbits * 4 + 7) // 8 + 4

abc_blocks = []
while p < len(raw) - 2:
    tag_code_len = struct.unpack('<H', raw[p:p+2])[0]
    p += 2
    code = tag_code_len >> 6
    length = tag_code_len & 0x3F
    if length == 0x3F:
        length = struct.unpack('<I', raw[p:p+4])[0]
        p += 4
    tag_data = raw[p:p+length]
    p += length
    if code in (82, 72):
        abc_blocks.append(tag_data)

abc = abc_blocks[1584]
name_end = abc.find(b'\x00', 4)
abc_data = abc[name_end+1:]

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
    strings.append(abc_data[pos:pos+slen].decode('utf-8', errors='ignore'))
    pos += slen

print("Strings in Block 1584:")
for idx, s in enumerate(strings):
    if any(k in s for k in ['xml', 'ui', 'FLASHSITE', 'LANGUAGE', 'png', 'zip']):
        print(f"  {idx}: {s}")

# Let's find pushstring opcodes (0x2C)
for i in range(len(abc_data)-2):
    if abc_data[i] == 0x2C:
        val, _ = read_u30(abc_data, i+1)
        if val < len(strings):
            print(f"Offset {i}: pushstring '{strings[val]}' (index {val})")
