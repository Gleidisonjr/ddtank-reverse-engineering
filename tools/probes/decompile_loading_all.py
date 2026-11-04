import zlib
import struct

with open('projects/ddtank-server/www/flash/Loading.swf', 'rb') as f:
    raw = f.read()

body = zlib.decompress(raw[8:])

# Skip header
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
    if code in (82, 72): # DoABC
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

def read_s24(buf, idx):
    b0 = buf[idx]; b1 = buf[idx+1]; b2 = buf[idx+2]
    val = b0 | (b1 << 8) | (b2 << 16)
    if val & 0x800000:
        val -= 0x1000000
    return val, idx + 3

pos = 4 # skip minor, major
int_count, pos = read_u30(abc_data, pos)
integers = [0]
for _ in range(1, int_count):
    v, pos = read_u30(abc_data, pos)
    integers.append(v)

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
    kind = abc_data[pos]; pos += 1
    name_idx, pos = read_u30(abc_data, pos)
    namespaces.append((kind, strings[name_idx] if name_idx < len(strings) else ''))

ns_set_count, pos = read_u30(abc_data, pos)
ns_sets = [None]
for _ in range(1, ns_set_count):
    count, pos = read_u30(abc_data, pos)
    ns_list = []
    for _ in range(count):
        ns_idx, pos = read_u30(abc_data, pos)
        ns_list.append(namespaces[ns_idx] if ns_idx < len(namespaces) else None)
    ns_sets.append(ns_list)

multiname_count, pos = read_u30(abc_data, pos)
multinames = [None]
for _ in range(1, multiname_count):
    kind = abc_data[pos]; pos += 1
    if kind in (0x07, 0x0D): # QName, QNameA
        ns, pos = read_u30(abc_data, pos)
        name, pos = read_u30(abc_data, pos)
        prefix = namespaces[ns][1] if ns < len(namespaces) and namespaces[ns] else ''
        multinames.append(f"{prefix}::{strings[name]}" if prefix else strings[name])
    elif kind in (0x09, 0x0E): # Multiname, MultinameA
        name, pos = read_u30(abc_data, pos)
        ns_set, pos = read_u30(abc_data, pos)
        multinames.append(strings[name])
    elif kind in (0x1B, 0x1C): # MultinameL, MultinameLA
        ns_set, pos = read_u30(abc_data, pos)
        multinames.append("MultinameL")
    elif kind in (0x17,): # TypeName
        pos += 2
        multinames.append("TypeName")
    else:
        multinames.append(f"multiname_{kind}")

# Methods
method_count, pos = read_u30(abc_data, pos)
methods = []
for m_idx in range(method_count):
    param_count, pos = read_u30(abc_data, pos)
    return_type, pos = read_u30(abc_data, pos)
    param_types = []
    for _ in range(param_count):
        pt, pos = read_u30(abc_data, pos)
        param_types.append(pt)
    name_idx, pos = read_u30(abc_data, pos)
    flags = abc_data[pos]; pos += 1
    if flags & 0x08: # HAS_OPTIONAL
        opt_count, pos = read_u30(abc_data, pos)
        for _ in range(opt_count):
            _, pos = read_u30(abc_data, pos)
            _, pos = read_u30(abc_data, pos)
    if flags & 0x80: # HAS_PARAM_NAMES
        for _ in range(param_count):
            _, pos = read_u30(abc_data, pos)
    methods.append({
        'name': strings[name_idx] if name_idx < len(strings) else f'method_{m_idx}',
        'param_count': param_count
    })

# Metadata
meta_count, pos = read_u30(abc_data, pos)
for _ in range(meta_count):
    _, pos = read_u30(abc_data, pos)
    item_count, pos = read_u30(abc_data, pos)
    for _ in range(item_count):
        _, pos = read_u30(abc_data, pos)
        _, pos = read_u30(abc_data, pos)

# Classes
class_count, pos = read_u30(abc_data, pos)
classes = []
for c_idx in range(class_count):
    name_idx, pos = read_u30(abc_data, pos)
    super_idx, pos = read_u30(abc_data, pos)
    flags = abc_data[pos]; pos += 1
    if flags & 0x08: # PROTECTED_NS
        _, pos = read_u30(abc_data, pos)
    intf_count, pos = read_u30(abc_data, pos)
    for _ in range(intf_count):
        _, pos = read_u30(abc_data, pos)
    iinit, pos = read_u30(abc_data, pos)
    # traits
    trait_count, pos = read_u30(abc_data, pos)
    traits = []
    for _ in range(trait_count):
        tname, pos = read_u30(abc_data, pos)
        tkind = abc_data[pos]; pos += 1
        kind_type = tkind & 0x0F
        if kind_type in (0, 6): # Slot, Const
            _, pos = read_u30(abc_data, pos)
            _, pos = read_u30(abc_data, pos)
            vidx, pos = read_u30(abc_data, pos)
            if vidx != 0: pos += 1
        elif kind_type in (1, 2, 3): # Method, Getter, Setter
            disp_id, pos = read_u30(abc_data, pos)
            meth_id, pos = read_u30(abc_data, pos)
            traits.append((multinames[tname] if tname < len(multinames) else '', meth_id))
        elif kind_type == 4: # Class
            _, pos = read_u30(abc_data, pos)
            _, pos = read_u30(abc_data, pos)
        elif kind_type == 5: # Function
            _, pos = read_u30(abc_data, pos)
            _, pos = read_u30(abc_data, pos)
        if (tkind >> 4) & 0x04: # ATTR_Metadata
            mcount, pos = read_u30(abc_data, pos)
            for _ in range(mcount): _, pos = read_u30(abc_data, pos)
    classes.append({'name': multinames[name_idx] if name_idx < len(multinames) else '', 'traits': traits})

for c_idx in range(class_count):
    cinit, pos = read_u30(abc_data, pos)
    trait_count, pos = read_u30(abc_data, pos)
    for _ in range(trait_count):
        tname, pos = read_u30(abc_data, pos)
        tkind = abc_data[pos]; pos += 1
        kind_type = tkind & 0x0F
        if kind_type in (0, 6):
            _, pos = read_u30(abc_data, pos)
            _, pos = read_u30(abc_data, pos)
            vidx, pos = read_u30(abc_data, pos)
            if vidx != 0: pos += 1
        elif kind_type in (1, 2, 3):
            _, pos = read_u30(abc_data, pos)
            _, pos = read_u30(abc_data, pos)
        elif kind_type in (4, 5):
            _, pos = read_u30(abc_data, pos)
            _, pos = read_u30(abc_data, pos)
        if (tkind >> 4) & 0x04:
            mcount, pos = read_u30(abc_data, pos)
            for _ in range(mcount): _, pos = read_u30(abc_data, pos)

# Scripts
script_count, pos = read_u30(abc_data, pos)
for _ in range(script_count):
    sinit, pos = read_u30(abc_data, pos)
    trait_count, pos = read_u30(abc_data, pos)
    for _ in range(trait_count):
        tname, pos = read_u30(abc_data, pos)
        tkind = abc_data[pos]; pos += 1
        kind_type = tkind & 0x0F
        if kind_type in (0, 6):
            _, pos = read_u30(abc_data, pos)
            _, pos = read_u30(abc_data, pos)
            vidx, pos = read_u30(abc_data, pos)
            if vidx != 0: pos += 1
        elif kind_type in (1, 2, 3):
            _, pos = read_u30(abc_data, pos)
            _, pos = read_u30(abc_data, pos)
        elif kind_type in (4, 5):
            _, pos = read_u30(abc_data, pos)
            _, pos = read_u30(abc_data, pos)
        if (tkind >> 4) & 0x04:
            mcount, pos = read_u30(abc_data, pos)
            for _ in range(mcount): _, pos = read_u30(abc_data, pos)

# Method bodies
body_count, pos = read_u30(abc_data, pos)
method_bodies = {}
for _ in range(body_count):
    m_idx, pos = read_u30(abc_data, pos)
    max_stack, pos = read_u30(abc_data, pos)
    local_count, pos = read_u30(abc_data, pos)
    init_scope_depth, pos = read_u30(abc_data, pos)
    max_scope_depth, pos = read_u30(abc_data, pos)
    code_length, pos = read_u30(abc_data, pos)
    code_bytes = abc_data[pos:pos+code_length]
    pos += code_length
    ex_count, pos = read_u30(abc_data, pos)
    exceptions = []
    for _ in range(ex_count):
        from_ip, pos = read_u30(abc_data, pos)
        to_ip, pos = read_u30(abc_data, pos)
        target_ip, pos = read_u30(abc_data, pos)
        exc_type, pos = read_u30(abc_data, pos)
        var_name, pos = read_u30(abc_data, pos)
        exceptions.append((from_ip, to_ip, target_ip, exc_type))
    tcount, pos = read_u30(abc_data, pos)
    for _ in range(tcount):
        tname, pos = read_u30(abc_data, pos)
        tkind = abc_data[pos]; pos += 1
        kind_type = tkind & 0x0F
        if kind_type in (0, 6):
            _, pos = read_u30(abc_data, pos)
            _, pos = read_u30(abc_data, pos)
            vidx, pos = read_u30(abc_data, pos)
            if vidx != 0: pos += 1
        elif kind_type in (1, 2, 3):
            _, pos = read_u30(abc_data, pos)
            _, pos = read_u30(abc_data, pos)
        elif kind_type in (4, 5):
            _, pos = read_u30(abc_data, pos)
            _, pos = read_u30(abc_data, pos)
        if (tkind >> 4) & 0x04:
            mcount, pos = read_u30(abc_data, pos)
            for _ in range(mcount): _, pos = read_u30(abc_data, pos)
    method_bodies[m_idx] = {'code': code_bytes, 'exceptions': exceptions}

print("Found methods in classes:")
for c in classes:
    print("Class:", c['name'])
    for tname, midx in c['traits']:
        print(f"   Trait: {tname} -> method {midx}")

# Let's write a function to disassemble any method body
def disasm(code):
    lines = []
    i = 0
    while i < len(code):
        ip = i
        op = code[i]; i += 1
        # Opcodes with multiname
        if op in (0x66, 0x60, 0x61, 0x5D, 0x5E, 0x4A, 0x46, 0x4F, 0x59):
            mn_idx, i = read_u30(code, i)
            mname = multinames[mn_idx] if mn_idx < len(multinames) else f"mn_{mn_idx}"
            if op in (0x46, 0x4F, 0x4A):
                argc, i = read_u30(code, i)
                lines.append(f"{ip:4d}: 0x{op:02x} {mname} (argc={argc})")
            else:
                lines.append(f"{ip:4d}: 0x{op:02x} {mname}")
        elif op in (0x2C,): # pushstring
            s_idx, i = read_u30(code, i)
            s = repr(strings[s_idx] if s_idx < len(strings) else f"str_{s_idx}")
            lines.append(f"{ip:4d}: pushstring {s}")
        elif op in (0x24, 0xC5): # pushbyte
            b = code[i]; i += 1
            lines.append(f"{ip:4d}: pushbyte {b}")
        elif op in (0x25,): # pushshort
            v, i = read_u30(code, i)
            lines.append(f"{ip:4d}: pushshort {v}")
        elif op in (0x26,): lines.append(f"{ip:4d}: pushtrue")
        elif op in (0x27,): lines.append(f"{ip:4d}: pushfalse")
        elif op in (0x28,): lines.append(f"{ip:4d}: pushnan")
        elif op in (0x20,): lines.append(f"{ip:4d}: pushnull")
        elif op in (0x21,): lines.append(f"{ip:4d}: pushundefined")
        elif op in (0xD0, 0xD1, 0xD2, 0xD3):
            lines.append(f"{ip:4d}: getlocal_{op - 0xD0}")
        elif op in (0xD4, 0xD5, 0xD6, 0xD7):
            lines.append(f"{ip:4d}: setlocal_{op - 0xD4 + 1}")
        elif op in (0x62,):
            loc, i = read_u30(code, i)
            lines.append(f"{ip:4d}: getlocal {loc}")
        elif op in (0x63,):
            loc, i = read_u30(code, i)
            lines.append(f"{ip:4d}: setlocal {loc}")
        elif op in (0x47,): lines.append(f"{ip:4d}: returnvoid")
        elif op in (0x48,): lines.append(f"{ip:4d}: returnvalue")
        elif op in (0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x0F): # jumps / branches
            target, i = read_s24(code, i)
            lines.append(f"{ip:4d}: branch_0x{op:02x} -> {ip + 4 + target}")
        elif op in (0x09,): lines.append(f"{ip:4d}: label")
        elif op in (0x08,): lines.append(f"{ip:4d}: kill")
        elif op in (0x03,): lines.append(f"{ip:4d}: throw")
        elif op in (0xA0,): lines.append(f"{ip:4d}: add")
        elif op in (0xA1,): lines.append(f"{ip:4d}: subtract")
        elif op in (0x80,): lines.append(f"{ip:4d}: coerce_any")
        elif op in (0x85,): lines.append(f"{ip:4d}: coerce_s")
        elif op in (0x86,): lines.append(f"{ip:4d}: astype")
        elif op in (0x30,): lines.append(f"{ip:4d}: constructsuper")
        elif op in (0x49,):
            argc, i = read_u30(code, i)
            lines.append(f"{ip:4d}: construct (argc={argc})")
        elif op in (0x42,):
            argc, i = read_u30(code, i)
            lines.append(f"{ip:4d}: constructprop (argc={argc})")
        else:
            lines.append(f"{ip:4d}: byte 0x{op:02x}")
    return lines

for c in classes:
    for tname, midx in c['traits']:
        if midx in method_bodies:
            print(f"\n==================== METHOD {tname} (ID {midx}) ====================")
            body = method_bodies[midx]
            print(f"Exceptions: {body['exceptions']}")
            for line in disasm(body['code']):
                print("  ", line)
