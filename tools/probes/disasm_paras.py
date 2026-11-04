import struct

with open('targets/dd-classico/extracted/dumped/flash_assets/1.swf', 'rb') as f:
    raw = f.read()

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

namespace_count, pos = read_u30(abc_data, pos)
namespaces = [None]
for _ in range(1, namespace_count):
    kind = abc_data[pos]; pos += 1
    name_idx, pos = read_u30(abc_data, pos)
    namespaces.append((kind, strings[name_idx] if name_idx < len(strings) else ''))

ns_set_count, pos = read_u30(abc_data, pos)
ns_sets = [None]
for _ in range(1, ns_set_count):
    count, pos = read_u30(abc_data, pos)
    s = []
    for _ in range(count):
        ns_idx, pos = read_u30(abc_data, pos)
        s.append(ns_idx)
    ns_sets.append(s)

multiname_count, pos = read_u30(abc_data, pos)
multinames = [None]
for _ in range(1, multiname_count):
    kind = abc_data[pos]; pos += 1
    if kind in (0x07, 0x0D): # QName, QNameA
        ns, pos = read_u30(abc_data, pos)
        name, pos = read_u30(abc_data, pos)
        multinames.append(f'{strings[name]}' if name < len(strings) else f'name_{name}')
    elif kind in (0x09, 0x0E): # Multiname, MultinameA
        name, pos = read_u30(abc_data, pos)
        ns_set, pos = read_u30(abc_data, pos)
        multinames.append(f'{strings[name]}' if name < len(strings) else f'name_{name}')
    elif kind in (0x0F, 0x10):
        name, pos = read_u30(abc_data, pos)
        multinames.append(f'{strings[name]}' if name < len(strings) else f'name_{name}')
    elif kind in (0x11, 0x12):
        multinames.append('RTQNameL')
    elif kind in (0x1B, 0x1C):
        ns_set, pos = read_u30(abc_data, pos)
        multinames.append('MultinameL')
    elif kind in (0x1D,):
        type_name, pos = read_u30(abc_data, pos)
        param_count, pos = read_u30(abc_data, pos)
        for _ in range(param_count): _, pos = read_u30(abc_data, pos)
        multinames.append('TypeName')
    else:
        break

code = bytes.fromhex('f1951df079d030f07bd0d06680035981134f940301f07cd0d06680035982134f920301f07dd0d06680035983134f930301f07ed06680032ca11d46841301120f0000f08001d0d06680036685134f950301f08201d06680036686134687130024000e000000f08501d0d06680035988134f900301f08601d0d06680035989134f910301f0870147')

p = 0
while p < len(code):
    b = code[p]
    p += 1
    if b == 0xd0:
        print('getlocal_0')
    elif b == 0x30:
        print('pushscope')
    elif b == 0x66: # getproperty
        idx, p = read_u30(code, p)
        print(f'getproperty {idx} ({multinames[idx]})')
    elif b == 0x59: # getdescendants
        idx, p = read_u30(code, p)
        print(f'getdescendants {idx} ({multinames[idx]})')
    elif b == 0x4f: # callpropvoid
        idx, p = read_u30(code, p)
        argc, p = read_u30(code, p)
        print(f'callpropvoid {idx} ({multinames[idx]}), argc={argc}')
    elif b == 0x46: # callproperty
        idx, p = read_u30(code, p)
        argc, p = read_u30(code, p)
        print(f'callproperty {idx} ({multinames[idx]}), argc={argc}')
    elif b == 0x2c: # pushstring
        idx, p = read_u30(code, p)
        print(f'pushstring {idx} ("{strings[idx]}")')
    elif b == 0x47:
        print('returnvoid')
    elif b in (0xf0, 0xf1): # debugline, debugfile
        p += 1
        if b == 0xf1: p += 1
    elif b == 0x12: # iffalse
        offset = code[p] | (code[p+1] << 8) | (code[p+2] << 16)
        p += 3
        print(f'iffalse {offset}')
    elif b == 0x0e: # iftrue
        offset = code[p] | (code[p+1] << 8) | (code[p+2] << 16)
        p += 3
        print(f'iftrue {offset}')
    elif b == 0x24: # pushbyte
        print(f'pushbyte {code[p]}')
        p += 1
    else:
        print(f'byte {hex(b)}')
