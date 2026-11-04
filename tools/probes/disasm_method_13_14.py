import zlib, struct

with open('projects/ddtank-server/www/flash/Loading.swf', 'rb') as f:
    raw = f.read()

body = zlib.decompress(raw[8:])
p = 0
nbits = body[0] >> 3
p += (5 + nbits * 4 + 7) // 8 + 4
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

abc = abc_blocks[4]
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
        multinames.append(f'{strings[name]}' if name < len(strings) else f'name_{name}')
    elif kind in (0x09, 0x0E):
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

method_count, pos = read_u30(abc_data, pos)
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

meta_count, pos = read_u30(abc_data, pos)
for _ in range(meta_count):
    _, pos = read_u30(abc_data, pos)
    ic, pos = read_u30(abc_data, pos)
    for _ in range(ic): _, pos = read_u30(abc_data, pos); _, pos = read_u30(abc_data, pos)

class_count, pos = read_u30(abc_data, pos)
for c_idx in range(class_count):
    _, pos = read_u30(abc_data, pos); _, pos = read_u30(abc_data, pos)
    flags = abc_data[pos]; pos += 1
    if flags & 0x08: _, pos = read_u30(abc_data, pos)
    ic, pos = read_u30(abc_data, pos)
    for _ in range(ic): _, pos = read_u30(abc_data, pos)
    _, pos = read_u30(abc_data, pos)
    tc, pos = read_u30(abc_data, pos)
    for _ in range(tc):
        _, pos = read_u30(abc_data, pos)
        tk = abc_data[pos]; pos += 1
        kt = tk & 0x0F
        if kt in (0, 6):
            _, pos = read_u30(abc_data, pos); _, pos = read_u30(abc_data, pos)
            vidx, pos = read_u30(abc_data, pos)
            if vidx != 0: pos += 1
        elif kt in (1, 2, 3):
            _, pos = read_u30(abc_data, pos); _, pos = read_u30(abc_data, pos)
        elif kt in (4, 5):
            _, pos = read_u30(abc_data, pos); _, pos = read_u30(abc_data, pos)
        if (tk >> 4) & 0x04:
            mc, pos = read_u30(abc_data, pos)
            for _ in range(mc): _, pos = read_u30(abc_data, pos)

for c_idx in range(class_count):
    _, pos = read_u30(abc_data, pos)
    tc, pos = read_u30(abc_data, pos)
    for _ in range(tc):
        _, pos = read_u30(abc_data, pos)
        tk = abc_data[pos]; pos += 1
        kt = tk & 0x0F
        if kt in (0, 6):
            _, pos = read_u30(abc_data, pos); _, pos = read_u30(abc_data, pos)
            vidx, pos = read_u30(abc_data, pos)
            if vidx != 0: pos += 1
        elif kt in (1, 2, 3):
            _, pos = read_u30(abc_data, pos); _, pos = read_u30(abc_data, pos)
        elif kt in (4, 5):
            _, pos = read_u30(abc_data, pos); _, pos = read_u30(abc_data, pos)
        if (tk >> 4) & 0x04:
            mc, pos = read_u30(abc_data, pos)
            for _ in range(mc): _, pos = read_u30(abc_data, pos)

script_count, pos = read_u30(abc_data, pos)
for s_idx in range(script_count):
    _, pos = read_u30(abc_data, pos)
    tc, pos = read_u30(abc_data, pos)
    for _ in range(tc):
        _, pos = read_u30(abc_data, pos)
        tk = abc_data[pos]; pos += 1
        kt = tk & 0x0F
        if kt in (0, 6):
            _, pos = read_u30(abc_data, pos); _, pos = read_u30(abc_data, pos)
            vidx, pos = read_u30(abc_data, pos)
            if vidx != 0: pos += 1
        elif kt in (1, 2, 3):
            _, pos = read_u30(abc_data, pos); _, pos = read_u30(abc_data, pos)
        elif kt in (4, 5):
            _, pos = read_u30(abc_data, pos); _, pos = read_u30(abc_data, pos)
        if (tk >> 4) & 0x04:
            mc, pos = read_u30(abc_data, pos)
            for _ in range(mc): _, pos = read_u30(abc_data, pos)

body_count, pos = read_u30(abc_data, pos)
b_bodies = {}
for b_idx in range(body_count):
    m_idx, pos = read_u30(abc_data, pos)
    stack, pos = read_u30(abc_data, pos)
    local_count, pos = read_u30(abc_data, pos)
    init_scope, pos = read_u30(abc_data, pos)
    max_scope, pos = read_u30(abc_data, pos)
    code_length, pos = read_u30(abc_data, pos)
    code = abc_data[pos:pos+code_length]
    pos += code_length
    ex_count, pos = read_u30(abc_data, pos)
    for _ in range(ex_count):
        _, pos = read_u30(abc_data, pos); _, pos = read_u30(abc_data, pos)
        _, pos = read_u30(abc_data, pos); _, pos = read_u30(abc_data, pos)
        _, pos = read_u30(abc_data, pos)
    tc, pos = read_u30(abc_data, pos)
    for _ in range(tc):
        _, pos = read_u30(abc_data, pos)
        tk = abc_data[pos]; pos += 1
        kt = tk & 0x0F
        if kt in (0, 6):
            _, pos = read_u30(abc_data, pos); _, pos = read_u30(abc_data, pos)
            vidx, pos = read_u30(abc_data, pos)
            if vidx != 0: pos += 1
        elif kt in (1, 2, 3):
            _, pos = read_u30(abc_data, pos); _, pos = read_u30(abc_data, pos)
        elif kt in (4, 5):
            _, pos = read_u30(abc_data, pos); _, pos = read_u30(abc_data, pos)
        if (tk >> 4) & 0x04:
            mc, pos = read_u30(abc_data, pos)
            for _ in range(mc): _, pos = read_u30(abc_data, pos)
    b_bodies[m_idx] = code

def disasm_safe(code):
    p = 0
    lines = []
    while p < len(code):
        op = code[p]; p += 1
        if op == 0xd0: lines.append('getlocal_0')
        elif op == 0xd1: lines.append('getlocal_1')
        elif op == 0xd2: lines.append('getlocal_2')
        elif op == 0xd3: lines.append('getlocal_3')
        elif op == 0x30: lines.append('pushscope')
        elif op == 0x47: lines.append('returnvoid')
        elif op == 0x60:
            idx, p = read_u30(code, p)
            mn = multinames[idx] if idx < len(multinames) else f'mn_{idx}'
            lines.append(f'getlex {mn}')
        elif op == 0x66:
            idx, p = read_u30(code, p)
            mn = multinames[idx] if idx < len(multinames) else f'mn_{idx}'
            lines.append(f'getproperty {mn}')
        elif op == 0x61:
            idx, p = read_u30(code, p)
            mn = multinames[idx] if idx < len(multinames) else f'mn_{idx}'
            lines.append(f'setproperty {mn}')
        elif op == 0x4f:
            idx, p = read_u30(code, p); argc, p = read_u30(code, p)
            mn = multinames[idx] if idx < len(multinames) else f'mn_{idx}'
            lines.append(f'callpropvoid {mn}(argc={argc})')
        elif op == 0x46:
            idx, p = read_u30(code, p); argc, p = read_u30(code, p)
            mn = multinames[idx] if idx < len(multinames) else f'mn_{idx}'
            lines.append(f'callproperty {mn}(argc={argc})')
        elif op == 0x2c:
            idx, p = read_u30(code, p)
            s = strings[idx] if idx < len(strings) else f'str_{idx}'
            lines.append(f'pushstring "{s}"')
        elif op == 0x24:
            lines.append(f'pushbyte {code[p]}'); p += 1
        elif op in (0xf0, 0xf1):
            p += 1
            if op == 0xf1: p += 1
        else:
            lines.append(f'op 0x{op:02x}')
    return lines

for mid in [13, 14]:
    print(f'=== METHOD {mid} ===')
    for l in disasm_safe(b_bodies[mid]):
        print('  ', l)
