import zlib

with open('projects/ddtank-server/www/flash/Loading.swf', 'rb') as f:
    data = f.read()

body = zlib.decompress(data[8:])
abc_pos = body.find(b'Loading\x00')
abc_data = body[abc_pos+8:]

# Let's extract the string table properly
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

print(f"Total strings: {len(strings)}")
print("String 0x1b (27):", strings[27] if len(strings) > 27 else 'N/A')
print("String 0x79 (121):", strings[121] if len(strings) > 121 else 'N/A')
print("String 0x8a (138):", strings[138] if len(strings) > 138 else 'N/A')
print("String 0x7d (125):", strings[125] if len(strings) > 125 else 'N/A')

# Print strings from index 130 to 150
for i in range(125, min(len(strings), 145)):
    print(f"  String {i}: {strings[i]}")
