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
    tag_code_len = body[p] | (body[p+1] << 8)
    p += 2
    code = tag_code_len >> 6
    length = tag_code_len & 0x3F
    if length == 0x3F:
        length = body[p] | (body[p+1] << 8) | (body[p+2] << 16) | (body[p+3] << 24)
        p += 4
    if code in (82, 72):
        name_end = body.find(b'\x00', p+4)
        tag_data = body[name_end+1:p+length]
        break
    p += length

abc_data = tag_data

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

namespace_count, pos = read_u30(abc_data, pos)
namespaces = [None]
for _ in range(1, namespace_count):
    kind = abc_data[pos]; pos += 1
    name_idx, pos = read_u30(abc_data, pos)
    namespaces.append((kind, strings[name_idx] if name_idx < len(strings) else ''))

ns_set_count, pos = read_u30(abc_data, pos)
for _ in range(1, ns_set_count):
    count, pos = read_u30(abc_data, pos)
    for _ in range(count): _, pos = read_u30(abc_data, pos)

multiname_count, pos = read_u30(abc_data, pos)
multinames = [None]
for _ in range(1, multiname_count):
    kind = abc_data[pos]; pos += 1
    if kind in (0x07, 0x0D):
        ns, pos = read_u30(abc_data, pos)
        name, pos = read_u30(abc_data, pos)
        multinames.append(f"{namespaces[ns][1]}::{strings[name]}")
    elif kind in (0x09, 0x0E):
        name, pos = read_u30(abc_data, pos)
        ns_set, pos = read_u30(abc_data, pos)
        multinames.append(f"{strings[name]}")
    elif kind in (0x1B, 0x1C):
        name, pos = read_u30(abc_data, pos)
        ns_set, pos = read_u30(abc_data, pos)
        multinames.append(f"@{strings[name]}")
    elif kind in (0x17,):
        pos += 2
        multinames.append("TypeName")
    else:
        multinames.append(f"kind_{kind}")

body_offset = 5115 + 240
code = abc_data[body_offset:body_offset+250]

i = 0
while i < len(code):
    op = code[i]
    ip = i + 240
    i += 1
    if op in (0x66, 0x60, 0x61, 0x5D, 0x4A, 0x46, 0x4F):
        val, i = read_u30(code, i)
        mname = multinames[val] if val < len(multinames) else f"multi_{val}"
        if op in (0x46, 0x4F, 0x4A):
            argc, i = read_u30(code, i)
            print(f"{ip:3d}: op 0x{op:02x} {mname} argc={argc}")
        else:
            print(f"{ip:3d}: op 0x{op:02x} {mname}")
    elif op in (0x2C,):
        val, i = read_u30(code, i)
        sname = strings[val] if val < len(strings) else f"str_{val}"
        print(f"{ip:3d}: pushstring '{sname}'")
    elif op in (0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18):
        target = code[i] | (code[i+1] << 8) | (code[i+2] << 16)
        if target & 0x800000: target -= 0x1000000
        i += 3
        print(f"{ip:3d}: branch 0x{op:02x} target={ip+4+target}")
    elif op in (0x24, 0x25, 0x26, 0x27, 0x28, 0xD0, 0xD1, 0xD2, 0xD3, 0x47, 0x48, 0x09, 0x03):
        print(f"{ip:3d}: op 0x{op:02x}")
