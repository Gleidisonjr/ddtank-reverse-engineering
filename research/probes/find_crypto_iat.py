import struct

with open(r'targets/district-187/client-rebirth/TheRaw.exe', 'rb') as f:
    exe = f.read()

e_lfanew = struct.unpack_from('<I', exe, 0x3c)[0]
opt_header = e_lfanew + 24
import_rva = struct.unpack_from('<I', exe, opt_header + 104)[0]
image_base = struct.unpack_from('<I', exe, opt_header + 28)[0]
print(f"ImageBase: {hex(image_base)}, ImportRVA: {hex(import_rva)}")

num_sec = struct.unpack_from('<H', exe, e_lfanew+6)[0]
opt_size = struct.unpack_from('<H', exe, e_lfanew+20)[0]
sec_start = opt_header + opt_size
sections = []
for i in range(num_sec):
    s = exe[sec_start + i*40 : sec_start + (i+1)*40]
    sections.append((struct.unpack_from('<I', s, 12)[0], struct.unpack_from('<I', s, 20)[0], struct.unpack_from('<I', s, 16)[0]))

def rva2raw(rva):
    for va, raw, sz in sections:
        if va <= rva < va + sz:
            return raw + (rva - va)
    return None

imp_off = rva2raw(import_rva)
crypto_funcs = {}

while True:
    desc = exe[imp_off:imp_off+20]
    if not any(desc): break
    ilt_rva = struct.unpack_from('<I', desc, 0)[0]
    name_rva = struct.unpack_from('<I', desc, 12)[0]
    iat_rva = struct.unpack_from('<I', desc, 16)[0]
    name = exe[rva2raw(name_rva):exe.find(b'\x00', rva2raw(name_rva))].decode('latin1')
    if 'crypt' in name.lower() or 'advapi' in name.lower():
        curr_ilt = rva2raw(ilt_rva)
        curr_iat_va = image_base + iat_rva
        idx = 0
        while True:
            entry = struct.unpack_from('<I', exe, curr_ilt + idx*4)[0]
            if entry == 0: break
            if not (entry & 0x80000000):
                hint_raw = rva2raw(entry)
                func_name = exe[hint_raw+2:exe.find(b'\x00', hint_raw+2)].decode('latin1')
                if 'Crypt' in func_name:
                    crypto_funcs[func_name] = curr_iat_va + idx*4
            idx += 1
    imp_off += 20

print("Crypto functions in TheRaw.exe IAT:")
for fn, va in crypto_funcs.items():
    print(f"  {fn:<20}: VA {hex(va)}")
    # Find calls
    pat = b'\xff\x15' + struct.pack('<I', va)
    idx = 0
    while True:
        pos = exe.find(pat, idx)
        if pos == -1: break
        call_va = image_base + sections[0][0] + (pos - sections[0][1])
        print(f"    called at VA: {hex(call_va)} (raw: {hex(pos)})")
        idx = pos + 1
