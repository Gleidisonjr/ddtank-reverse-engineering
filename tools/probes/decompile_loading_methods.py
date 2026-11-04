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
        multinames.append(f"{strings[name]}")
    elif kind in (0x1B, 0x1C): # MultinameA
        name, pos = read_u30(abc_data, pos)
        ns_set, pos = read_u30(abc_data, pos)
        multinames.append(f"@{strings[name]}")
    elif kind in (0x17,): # TypeName
        pos += 2
        multinames.append("TypeName")
    else:
        multinames.append(f"kind_{kind}")

# Methods
method_count, pos = read_u30(abc_data, pos)
methods = []
for m in range(method_count):
    param_count, pos = read_u30(abc_data, pos)
    return_type, pos = read_u30(abc_data, pos)
    for _ in range(param_count):
        _, pos = read_u30(abc_data, pos)
    name_idx, pos = read_u30(abc_data, pos)
    flags = abc_data[pos]
    pos += 1
    if flags & 0x08: # HAS_OPTIONAL
        opt_count, pos = read_u30(abc_data, pos)
        for _ in range(opt_count):
            _, pos = read_u30(abc_data, pos)
            _, pos = read_u30(abc_data, pos)
    if flags & 0x80: # HAS_PARAM_NAMES
        for _ in range(param_count):
            _, pos = read_u30(abc_data, pos)
    methods.append(strings[name_idx] if name_idx < len(strings) else f"m_{m}")

# Metadata
metadata_count, pos = read_u30(abc_data, pos)
for _ in range(metadata_count):
    _, pos = read_u30(abc_data, pos)
    item_count, pos = read_u30(abc_data, pos)
    for _ in range(item_count):
        _, pos = read_u30(abc_data, pos)
        _, pos = read_u30(abc_data, pos)

# Traits helper
def read_traits(p):
    tcount, p = read_u30(abc_data, p)
    traits = []
    for _ in range(tcount):
        tname, p = read_u30(abc_data, p)
        tkind = abc_data[p]
        p += 1
        kind_id = tkind & 0x0F
        if kind_id in (0, 6): # Slot, Const
            _, p = read_u30(abc_data, p)
            type_name, p = read_u30(abc_data, p)
            val_idx, p = read_u30(abc_data, p)
            if val_idx != 0:
                p += 1 # val_kind
        elif kind_id in (1, 2, 3): # Method, Getter, Setter
            disp_id, p = read_u30(abc_data, p)
            method_idx, p = read_u30(abc_data, p)
            traits.append((multinames[tname] if tname < len(multinames) else tname, method_idx))
        elif kind_id == 4: # Class
            _, p = read_u30(abc_data, p)
            _, p = read_u30(abc_data, p)
        elif kind_id == 5: # Function
            _, p = read_u30(abc_data, p)
            _, p = read_u30(abc_data, p)
        if (tkind >> 4) & 0x04: # Metadata
            mcount, p = read_u30(abc_data, p)
            for _ in range(mcount):
                _, p = read_u30(abc_data, p)
    return traits, p

# Instances
class_count, pos = read_u30(abc_data, pos)
print(f"Class count: {class_count}")
instance_traits = []
for c in range(class_count):
    name_idx, pos = read_u30(abc_data, pos)
    super_idx, pos = read_u30(abc_data, pos)
    flags = abc_data[pos]
    pos += 1
    if flags & 0x08: # ProtectedNS
        _, pos = read_u30(abc_data, pos)
    intf_count, pos = read_u30(abc_data, pos)
    for _ in range(intf_count):
        _, pos = read_u30(abc_data, pos)
    iinit, pos = read_u30(abc_data, pos)
    tr, pos = read_traits(pos)
    instance_traits.append((multinames[name_idx] if name_idx < len(multinames) else name_idx, iinit, tr))

for c in range(class_count):
    cinit, pos = read_u30(abc_data, pos)
    ctr, pos = read_traits(pos)

# Scripts
script_count, pos = read_u30(abc_data, pos)
for _ in range(script_count):
    _, pos = read_u30(abc_data, pos)
    str_list, pos = read_traits(pos)

# Method bodies
body_count, pos = read_u30(abc_data, pos)
print(f"Body count: {body_count}")
for b in range(body_count):
    method_idx, pos = read_u30(abc_data, pos)
    max_stack, pos = read_u30(abc_data, pos)
    local_count, pos = read_u30(abc_data, pos)
    init_scope_depth, pos = read_u30(abc_data, pos)
    max_scope_depth, pos = read_u30(abc_data, pos)
    code_len, pos = read_u30(abc_data, pos)
    code = abc_data[pos:pos+code_len]
    pos += code_len
    exc_count, pos = read_u30(abc_data, pos)
    for _ in range(exc_count):
        _, pos = read_u30(abc_data, pos)
        _, pos = read_u30(abc_data, pos)
        _, pos = read_u30(abc_data, pos)
        _, pos = read_u30(abc_data, pos)
        _, pos = read_u30(abc_data, pos)
    btr, pos = read_traits(pos)
    
    m_name = methods[method_idx] if method_idx < len(methods) else f"m_{method_idx}"
    # Check if this method matches any trait
    trait_names = []
    for cname, iinit, tr in instance_traits:
        if iinit == method_idx:
            trait_names.append(f"{cname}::constructor")
        for tname, midx in tr:
            if midx == method_idx:
                trait_names.append(f"{cname}::{tname}")
    
    # Let's inspect __onConfigLoadComplete or init or createLogin
    label = "/".join(trait_names) if trait_names else m_name
    if any(k in label.lower() for k in ['config', 'init', 'select', 'login', 'load']):
        print(f"\n=== Method {method_idx}: {label} (len={code_len}) ===")
        # Disassemble basic instructions
        cp = 0
        while cp < min(code_len, 200):
            op = code[cp]
            cp += 1
            if op == 0x2C: # pushstring
                sidx, cp = read_u30(code, cp)
                sval = strings[sidx] if sidx < len(strings) else f"str_{sidx}"
                print(f"  [{cp-2:4d}] pushstring '{sval}'")
            elif op in (0x66, 0x60): # getproperty, getlex
                midx, cp = read_u30(code, cp)
                mval = multinames[midx] if midx < len(multinames) else f"multi_{midx}"
                print(f"  [{cp-2:4d}] {'getproperty' if op == 0x66 else 'getlex'} {mval}")
            elif op in (0x68, 0x61): # initproperty, setproperty
                midx, cp = read_u30(code, cp)
                mval = multinames[midx] if midx < len(multinames) else f"multi_{midx}"
                print(f"  [{cp-2:4d}] {'setproperty' if op == 0x61 else 'initproperty'} {mval}")
            elif op in (0x46, 0x4F): # callproperty, callpropvoid
                midx, cp = read_u30(code, cp)
                argc, cp = read_u30(code, cp)
                mval = multinames[midx] if midx < len(multinames) else f"multi_{midx}"
                print(f"  [{cp-3:4d}] {'callproperty' if op == 0x46 else 'callpropvoid'} {mval}(argc={argc})")
            elif op == 0x5D: # findpropstrict
                midx, cp = read_u30(code, cp)
                mval = multinames[midx] if midx < len(multinames) else f"multi_{midx}"
                print(f"  [{cp-2:4d}] findpropstrict {mval}")
            elif op == 0x47: # returnvoid
                print(f"  [{cp-1:4d}] returnvoid")
                break
