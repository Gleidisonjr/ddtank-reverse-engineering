import struct

def parse_abc(data):
    p = 0
    minor = struct.unpack('<H', data[p:p+2])[0]; p += 2
    major = struct.unpack('<H', data[p:p+2])[0]; p += 2
    
    def read_u30():
        nonlocal p
        res, shift = 0, 0
        while True:
            b = data[p]
            p += 1
            res |= (b & 0x7f) << shift
            if (b & 0x80) == 0: break
            shift += 7
        return res

    def read_s32():
        u = read_u30()
        return u - 0x100000000 if u & 0x80000000 else u

    int_cnt = read_u30()
    ints = [0] + [read_s32() for _ in range(int_cnt - 1)] if int_cnt > 0 else [0]
    uint_cnt = read_u30()
    uints = [0] + [read_u30() for _ in range(uint_cnt - 1)] if uint_cnt > 0 else [0]
    dbl_cnt = read_u30()
    doubles = [0.0]
    for _ in range(dbl_cnt - 1 if dbl_cnt > 0 else 0):
        d = struct.unpack('<d', data[p:p+8])[0]
        doubles.append(d)
        p += 8

    str_cnt = read_u30()
    strings = ['']
    for _ in range(str_cnt - 1 if str_cnt > 0 else 0):
        slen = read_u30()
        s = data[p:p+slen].decode('utf-8', errors='replace')
        p += slen
        strings.append(s)

    ns_cnt = read_u30()
    namespaces = [('', 0)]
    for _ in range(ns_cnt - 1 if ns_cnt > 0 else 0):
        kind = data[p]; p += 1
        name_idx = read_u30()
        namespaces.append((strings[name_idx] if name_idx < len(strings) else '', kind))

    ns_set_cnt = read_u30()
    ns_sets = [[]]
    for _ in range(ns_set_cnt - 1 if ns_set_cnt > 0 else 0):
        cnt = read_u30()
        ns_sets.append([read_u30() for _ in range(cnt)])

    mn_cnt = read_u30()
    multinames = ['']
    for _ in range(mn_cnt - 1 if mn_cnt > 0 else 0):
        kind = data[p]; p += 1
        if kind in (0x07, 0x0D):
            ns_idx = read_u30()
            name_idx = read_u30()
            multinames.append(strings[name_idx] if name_idx < len(strings) else f'mn_{name_idx}')
        elif kind in (0x09, 0x0E):
            name_idx = read_u30()
            ns_set_idx = read_u30()
            multinames.append(strings[name_idx] if name_idx < len(strings) else f'mn_{name_idx}')
        elif kind in (0x1B, 0x1C):
            read_u30()
            multinames.append('[L]')
        elif kind in (0x0F, 0x10):
            name_idx = read_u30()
            multinames.append(strings[name_idx] if name_idx < len(strings) else f'mn_{name_idx}')
        elif kind in (0x11, 0x12):
            multinames.append('[RTL]')
        elif kind == 0x1D:
            qname_idx = read_u30()
            param_cnt = read_u30()
            for _ in range(param_cnt): read_u30()
            multinames.append(multinames[qname_idx] if qname_idx < len(multinames) else f'type_{qname_idx}')
        else:
            multinames.append(f'unknown_mn_0x{kind:02x}')

    # Methods
    method_cnt = read_u30()
    methods = []
    for m_idx in range(method_cnt):
        param_cnt = read_u30()
        ret_type = read_u30()
        params = [read_u30() for _ in range(param_cnt)]
        name_idx = read_u30()
        flags = data[p]; p += 1
        if flags & 0x08:
            opt_cnt = read_u30()
            for _ in range(opt_cnt): read_u30(); p += 1
        if flags & 0x80:
            for _ in range(param_cnt): read_u30()
        m_name = strings[name_idx] if name_idx < len(strings) else ''
        methods.append({'idx': m_idx, 'name': m_name, 'param_cnt': param_cnt})

    # Metadata
    meta_cnt = read_u30()
    for _ in range(meta_cnt):
        read_u30()
        for _ in range(read_u30()): read_u30(); read_u30()

    # Instances
    inst_cnt = read_u30()
    instances = []
    for _ in range(inst_cnt):
        name_idx = read_u30()
        super_name = read_u30()
        flags = data[p]; p += 1
        if flags & 0x08: read_u30()
        for _ in range(read_u30()): read_u30()
        iinit = read_u30()
        traits = []
        for _ in range(read_u30()):
            t_name_idx = read_u30()
            t_name = multinames[t_name_idx] if t_name_idx < len(multinames) else ''
            t_kind_byte = data[p]; p += 1
            t_kind = t_kind_byte & 0x0F
            if t_kind in (0, 6):
                s_id = read_u30(); t_idx = read_u30(); v = read_u30()
                if v != 0: p += 1
                traits.append((t_name, 'slot/const', None))
            elif t_kind in (1, 2, 3):
                disp_id = read_u30()
                m_id = read_u30()
                kind_str = {1: 'method', 2: 'getter', 3: 'setter'}[t_kind]
                traits.append((t_name, kind_str, m_id))
            elif t_kind in (4, 5):
                read_u30(); read_u30()
            if (t_kind_byte >> 4) & 0x04:
                for _ in range(read_u30()): read_u30()
        instances.append({'name': multinames[name_idx], 'iinit': iinit, 'traits': traits})

    # Classes
    class_traits = []
    for i in range(inst_cnt):
        cinit = read_u30()
        c_tr = []
        for _ in range(read_u30()):
            t_name_idx = read_u30()
            t_name = multinames[t_name_idx] if t_name_idx < len(multinames) else ''
            tk = data[p]; p += 1
            t_kind = tk & 0x0F
            if t_kind in (0, 6):
                s_id = read_u30(); t_idx = read_u30(); v = read_u30()
                v_kind = data[p] if v != 0 else 0
                if v != 0: p += 1
                val = None
                if v_kind == 0x03 and v < len(ints): val = ints[v]
                elif v_kind == 0x04 and v < len(uints): val = uints[v]
                elif v_kind == 0x01 and v < len(strings): val = strings[v]
                c_tr.append((t_name, 'static_const', val))
            elif t_kind in (1, 2, 3):
                disp_id = read_u30()
                m_id = read_u30()
                c_tr.append((t_name, 'static_method', m_id))
            elif t_kind in (4, 5):
                read_u30(); read_u30()
            if (tk >> 4) & 0x04:
                for _ in range(read_u30()): read_u30()
        class_traits.append({'cinit': cinit, 'traits': c_tr})

    # Scripts
    script_cnt = read_u30()
    for _ in range(script_cnt):
        sinit = read_u30()
        for _ in range(read_u30()):
            read_u30()
            tk = data[p]; p += 1
            if (tk & 0x0f) in (0, 6):
                read_u30(); read_u30(); v = read_u30()
                if v != 0: p += 1
            elif (tk & 0x0f) in (1, 2, 3, 4, 5):
                read_u30(); read_u30()
            if (tk >> 4) & 0x04:
                for _ in range(read_u30()): read_u30()

    # Method Bodies
    body_cnt = read_u30()
    bodies = {}
    for _ in range(body_cnt):
        m_idx = read_u30()
        max_stack = read_u30()
        local_cnt = read_u30()
        init_scope_depth = read_u30()
        max_scope_depth = read_u30()
        code_len = read_u30()
        code = data[p:p+code_len]
        p += code_len
        exc_cnt = read_u30()
        for _ in range(exc_cnt):
            read_u30(); read_u30(); read_u30(); read_u30(); read_u30()
        for _ in range(read_u30()):
            read_u30()
            tk = data[p]; p += 1
            if (tk & 0x0f) in (0, 6):
                read_u30(); read_u30(); v = read_u30()
                if v != 0: p += 1
            elif (tk & 0x0f) in (1, 2, 3, 4, 5):
                read_u30(); read_u30()
            if (tk >> 4) & 0x04:
                for _ in range(read_u30()): read_u30()
        bodies[m_idx] = code

    return instances, class_traits, methods, bodies, strings, ints, multinames

OPCODES = {
    0x24: ('pushbyte', 1),
    0x25: ('pushshort', 1),
    0x2D: ('pushint', 1),
    0x2E: ('pushuint', 1),
    0x2F: ('pushdouble', 1),
    0x2C: ('pushstring', 1),
    0x26: ('pushtrue', 0),
    0x27: ('pushfalse', 0),
    0x20: ('pushnull', 0),
    0x21: ('pushundefined', 0),
    0xD0: ('getlocal_0', 0),
    0xD1: ('getlocal_1', 0),
    0xD2: ('getlocal_2', 0),
    0xD3: ('getlocal_3', 0),
    0x62: ('getlocal', 1),
    0xD4: ('setlocal_0', 0),
    0xD5: ('setlocal_1', 0),
    0xD6: ('setlocal_2', 0),
    0xD7: ('setlocal_3', 0),
    0x63: ('setlocal', 1),
    0x66: ('getproperty', 1),
    0x61: ('setproperty', 1),
    0x68: ('initproperty', 1),
    0x60: ('getlex', 1),
    0x46: ('callproperty', 2),
    0x4F: ('callpropvoid', 2),
    0x45: ('callsuper', 2),
    0x4E: ('callsupervoid', 2),
    0x47: ('returnvoid', 0),
    0x48: ('returnvalue', 0),
    0x5D: ('findpropstrict', 1),
    0x5E: ('findproperty', 1),
    0xA0: ('add', 0),
    0xA1: ('subtract', 0),
    0xA2: ('multiply', 0),
    0xA3: ('divide', 0),
    0xA4: ('modulo', 0),
    0xA8: ('bitand', 0),
    0xA9: ('bitor', 0),
    0xAA: ('bitxor', 0),
    0xAB: ('lshift', 0),
    0xAC: ('rshift', 0),
    0xAD: ('urshift', 0),
    0x0C: ('ifnlt', 'branch'),
    0x0D: ('ifnle', 'branch'),
    0x0E: ('ifngt', 'branch'),
    0x0F: ('ifnge', 'branch'),
    0x10: ('jump', 'branch'),
    0x11: ('iftrue', 'branch'),
    0x12: ('iffalse', 'branch'),
    0x13: ('ifeq', 'branch'),
    0x14: ('ifne', 'branch'),
    0x15: ('iflt', 'branch'),
    0x16: ('ifle', 'branch'),
    0x17: ('ifgt', 'branch'),
    0x18: ('ifge', 'branch'),
}

def disasm_code(code, multinames, strings, ints):
    lines = []
    ip = 0
    
    def read_u30_from_code():
        nonlocal ip
        res, shift = 0, 0
        while True:
            b = code[ip]
            ip += 1
            res |= (b & 0x7f) << shift
            if (b & 0x80) == 0: break
            shift += 7
        return res

    while ip < len(code):
        cur_ip = ip
        op = code[ip]
        ip += 1
        if op in OPCODES:
            name, arg_type = OPCODES[op]
            if arg_type == 0:
                lines.append(f'{cur_ip:04x}: {name}')
            elif arg_type == 1:
                idx = read_u30_from_code()
                extra = ''
                if name in ('getproperty', 'setproperty', 'initproperty', 'getlex', 'findpropstrict', 'findproperty'):
                    extra = f' ({multinames[idx] if idx < len(multinames) else idx})'
                elif name == 'pushstring':
                    extra = f' ("{strings[idx] if idx < len(strings) else idx}")'
                elif name == 'pushint':
                    extra = f' ({ints[idx] if idx < len(ints) else idx})'
                elif name in ('pushbyte', 'pushshort'):
                    extra = f' ({idx})'
                lines.append(f'{cur_ip:04x}: {name} {idx}{extra}')
            elif arg_type == 2:
                idx = read_u30_from_code()
                argc = read_u30_from_code()
                mname = multinames[idx] if idx < len(multinames) else idx
                lines.append(f'{cur_ip:04x}: {name} {mname}, argc={argc}')
            elif arg_type == 'branch':
                if ip + 3 > len(code):
                    break
                b0 = code[ip]; b1 = code[ip+1]; b2 = code[ip+2]
                val = b0 | (b1 << 8) | (b2 << 16)
                if val & 0x800000: val -= 0x1000000
                ip += 3
                target = ip + val
                lines.append(f'{cur_ip:04x}: {name} -> 0x{target:04x}')
        else:
            lines.append(f'{cur_ip:04x}: 0x{op:02x}')
    return lines

if __name__ == '__main__':
    # Load 2.swf
    with open('targets/dd-classico/extracted/dumped/flash_assets/2.swf', 'rb') as f:
        raw = bytearray(f.read())
    if raw[:3] == b'CWS': raw[:3] = b'FWS'
    nbits = raw[8] >> 3
    pos = 8 + (5 + nbits * 4 + 7) // 8 + 4

    targets = ['road7th/comm/PackageIn', 'road7th/comm/PackageOut', 'road7th/comm/ByteSocket']
    target_data = {}

    while pos < len(raw):
        tcl = struct.unpack('<H', raw[pos:pos+2])[0]
        pos += 2
        code, tlen = tcl >> 6, tcl & 0x3F
        if tlen == 0x3F: tlen = struct.unpack('<I', raw[pos:pos+4])[0]; pos += 4
        if code == 82:
            d = raw[pos:pos+tlen]
            n_idx = d.find(b'\x00', 4)
            name = d[4:n_idx].decode('utf-8', errors='replace')
            if name in targets:
                target_data[name] = d[n_idx+1:]
        pos += tlen

    for name, abc in target_data.items():
        print(f'==============================================')
        print(f'CLASS: {name}')
        print(f'==============================================')
        insts, ctraits, methods, bodies, strings, ints, multinames = parse_abc(abc)
        for inst in insts:
            print(f'Instance: {inst["name"]}')
            for tname, tkind, mid in inst['traits']:
                if mid is not None and mid in bodies:
                    print(f'  -- Method: {tname} ({tkind}, m_id={mid}) --')
                    lines = disasm_code(bodies[mid], multinames, strings, ints)
                    for l in lines[:30]:
                        print(f'     {l}')
        for i, ct in enumerate(ctraits):
            print(f'Class Statics {i}:')
            for tname, tkind, val in ct['traits']:
                print(f'  static {tname} = {val}')

