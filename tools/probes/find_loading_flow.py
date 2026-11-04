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
        abc_blocks.append(tag_data)

abc = abc_blocks[0]
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

namespace_count, pos = read_u30(abc_data, pos)
namespaces = [None]
for _ in range(1, namespace_count):
    kind = abc_data[pos]
    pos += 1
    name_idx, pos = read_u30(abc_data, pos)
    namespaces.append((kind, strings[name_idx] if name_idx < len(strings) else ''))

ns_set_count, pos = read_u30(abc_data, pos)
for _ in range(1, ns_set_count):
    count, pos = read_u30(abc_data, pos)
    for _ in range(count):
        _, pos = read_u30(abc_data, pos)

multiname_count, pos = read_u30(abc_data, pos)
multinames = [None]
for _ in range(1, multiname_count):
    kind = abc_data[pos]
    pos += 1
    if kind in (0x07, 0x0D): # QName
        ns, pos = read_u30(abc_data, pos)
        name, pos = read_u30(abc_data, pos)
        multinames.append(f"{namespaces[ns][1]}::{strings[name]}")
    elif kind in (0x09, 0x0E): # Multiname
        name, pos = read_u30(abc_data, pos)
        ns_set, pos = read_u30(abc_data, pos)
        multinames.append(f"multiname::{strings[name]}")
    elif kind in (0x1B, 0x1C): # MultinameA
        name, pos = read_u30(abc_data, pos)
        ns_set, pos = read_u30(abc_data, pos)
        multinames.append(f"multinameA::{strings[name]}")
    elif kind in (0x17,): # TypeName
        pos += 2
        multinames.append("TypeName")
    else:
        multinames.append(f"kind_{kind}")

method_count, pos = read_u30(abc_data, pos)
print(f"Method count: {method_count}")

# Let's search in the remaining abc_data for references to string indices of __onConfigLoadComplete
target_strings = ['__onConfigLoadComplete', 'loadSelectList', 'loadConfig', 'LoginSelectList.ashx', 'md5.xml', 'DDT_Loading.swf']
target_indices = {strings.index(s): s for s in target_strings if s in strings}
print("Target indices:", target_indices)

# Search for findproperty / callprop / getproperty / pushstring in abc_data
for idx, s in target_indices.items():
    # pushstring opcode is 0x2C followed by u30 string index
    needle = bytes([0x2C, idx])
    offsets = [i for i in range(len(abc_data)) if abc_data.startswith(needle, i)]
    print(f"String '{s}' (index {idx}) referenced at offsets: {offsets}")
    for off in offsets:
        # print 50 bytes of bytecode around off
        chunk = abc_data[max(0, off-20):min(len(abc_data), off+50)]
        print(f"   Context at {off}: {chunk.hex()}")
