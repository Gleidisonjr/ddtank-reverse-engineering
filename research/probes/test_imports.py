import struct

def get_imports(path):
    with open(path, 'rb') as f:
        data = f.read()
    e_lfanew = struct.unpack_from('<I', data, 0x3c)[0]
    num_sections = struct.unpack_from('<H', data, e_lfanew + 6)[0]
    opt_header = e_lfanew + 24
    opt_size = struct.unpack_from('<H', data, e_lfanew + 20)[0]
    import_rva = struct.unpack_from('<I', data, opt_header + 104)[0]
    
    sections = []
    sec_start = opt_header + opt_size
    for i in range(num_sections):
        s_data = data[sec_start + i*40 : sec_start + (i+1)*40]
        s_va = struct.unpack_from('<I', s_data, 12)[0]
        s_raw = struct.unpack_from('<I', s_data, 20)[0]
        s_sz = struct.unpack_from('<I', s_data, 16)[0]
        sections.append((s_va, s_raw, s_sz))
        
    def rva2off(rva):
        for va, raw, sz in sections:
            if va <= rva < va + sz:
                return raw + (rva - va)
        return None

    imp_off = rva2off(import_rva)
    if not imp_off:
        return []
    imports = []
    while True:
        desc = data[imp_off:imp_off+20]
        if not any(desc): break
        name_rva = struct.unpack_from('<I', desc, 12)[0]
        name_off = rva2off(name_rva)
        if name_off:
            dll_name = data[name_off:data.find(b'\x00', name_off)].decode('latin1')
            imports.append(dll_name)
        imp_off += 20
    return imports

print("ApexGuard imports:", get_imports(r'targets/district-187/client-rebirth/ApexGuard.dll'))
print("D3DX9_43 imports:", get_imports(r'targets/district-187/client-rebirth/D3DX9_43.dll'))
