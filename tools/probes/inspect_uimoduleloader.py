import struct

with open('projects/ddtank-server/www/flash/1.swf', 'rb') as f:
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
        multinames.append(f"{namespaces[ns][1]}::{strings[name]}" if namespaces[ns][1] else strings[name])
    elif kind in (0x09, 0x0E):
        name, pos = read_u30(abc_data, pos)
        ns_set, pos = read_u30(abc_data, pos)
        multinames.append(strings[name])
    elif kind in (0x1B, 0x1C):
        ns_set, pos = read_u30(abc_data, pos)
        multinames.append("MultinameL")
    elif kind in (0x17,):
        pos += 2
        multinames.append("TypeName")
    else:
        multinames.append(f"mn_{kind}")

method_count, pos = read_u30(abc_data, pos)
methods = []
for m_idx in range(method_count):
    param_count, pos = read_u30(abc_data, pos)
    return_type, pos = read_u30(abc_data, pos)
    for _ in range(param_count): _, pos = read_u30(abc_data, pos)
    name_idx, pos = read_u30(abc_data, pos)
    flags = abc_data[pos]; pos += 1
    if flags & 0x08:
        opt_count, pos = read_u30(abc_data, pos)
        for _ in range(opt_count): _, pos = read_u30(abc_data, pos); _, pos = read_u30(abc_data, pos)
    if flags & 0x80:
        for _ in range(param_count): _, pos = read_u30(abc_data, pos)
    methods.append({'name': strings[name_idx] if name_idx < len(strings) else f'method_{m_idx}'})

meta_count, pos = read_u30(abc_data, pos)
for _ in range(meta_count):
    _, pos = read_u30(abc_data, pos)
    item_count, pos = read_u30(abc_data, pos)
    for _ in range(item_count): _, pos = read_u30(abc_data, pos); _, pos = read_u30(abc_data, pos)

class_count, pos = read_u30(abc_data, pos)
classes = []
for c_idx in range(class_count):
    name_idx, pos = read_u30(abc_data, pos)
    super_idx, pos = read_u30(abc_data, pos)
    flags = abc_data[pos]; pos += 1
    if flags & 0x08: _, pos = read_u30(abc_data, pos)
    intf_count, pos = read_u30(abc_data, pos)
    for _ in range(intf_count): _, pos = read_u30(abc_data, pos)
    iinit, pos = read_u30(abc_data, pos)
    trait_count, pos = read_u30(abc_data, pos)
    traits = []
    for _ in range(trait_count):
        tname, pos = read_u30(abc_data, pos)
        tkind = abc_data[pos]; pos += 1
        kind_type = tkind & 0x0F
        if kind_type in (0, 6):
            _, pos = read_u30(abc_data, pos); _, pos = read_u30(abc_data, pos)
            vidx, pos = read_u30(abc_data, pos)
            if vidx != 0: pos += 1
        elif kind_type in (1, 2, 3):
            disp_id, pos = read_u30(abc_data, pos)
            meth_id, pos = read_u30(abc_data, pos)
            traits.append((multinames[tname] if tname < len(multinames) else '', meth_id))
        elif kind_type in (4, 5):
            _, pos = read_u30(abc_data, pos); _, pos = read_u30(abc_data, pos)
        if (tkind >> 4) & 0x04:
            mcount, pos = read_u30(abc_data, pos)
            for _ in range(mcount): _, pos = read_u30(abc_data, pos)
    classes.append({'name': multinames[name_idx] if name_idx < len(multinames) else '', 'traits': traits})

for c in classes:
    if 'UIModuleLoader' in c['name']:
        print("Found UIModuleLoader class:", c['name'])
        for tname, midx in c['traits']:
            print(f"   Trait: {tname} -> method {midx}")
