import struct, capstone

with open(r'targets/district-187/client-rebirth/Game/GameClient.dll', 'rb') as f:
    dll = f.read()

# Find IAT address of send
# WS2_32.dll import
# In .text, find all "call dword ptr [IAT_send]" or "call ds:send"
# Let's search for IAT entry for ws2_32.dll

# Search for the string "send\x00"
send_str = dll.find(b'send\x00')
print(f"'send' string at raw: {hex(send_str)}")

# Find IAT entry referencing this hint/name table
# In x86 PE, ILT points to RVA of Hint/Name table.
# Let's write a quick PE import locator for ws2_32:send
e_lfanew = struct.unpack_from('<I', dll, 0x3c)[0]
opt_header = e_lfanew + 24
import_rva = struct.unpack_from('<I', dll, opt_header + 104)[0]

# sections
num_sec = struct.unpack_from('<H', dll, e_lfanew+6)[0]
opt_size = struct.unpack_from('<H', dll, e_lfanew+20)[0]
sec_start = opt_header + opt_size
sections = []
for i in range(num_sec):
    s = dll[sec_start + i*40 : sec_start + (i+1)*40]
    sections.append((struct.unpack_from('<I', s, 12)[0], struct.unpack_from('<I', s, 20)[0], struct.unpack_from('<I', s, 16)[0]))

def rva2raw(rva):
    for va, raw, sz in sections:
        if va <= rva < va + sz:
            return raw + (rva - va)
    return None

imp_off = rva2raw(import_rva)
iat_send_va = None

while True:
    desc = dll[imp_off:imp_off+20]
    if not any(desc): break
    ilt_rva = struct.unpack_from('<I', desc, 0)[0]
    name_rva = struct.unpack_from('<I', desc, 12)[0]
    iat_rva = struct.unpack_from('<I', desc, 16)[0]
    name = dll[rva2raw(name_rva):dll.find(b'\x00', rva2raw(name_rva))].decode('latin1')
    if 'ws2_32' in name.lower():
        print(f"Found WS2_32.dll at IAT RVA {hex(iat_rva)}")
        # iterate ILT/IAT
        curr_ilt = rva2raw(ilt_rva)
        curr_iat_va = 0x10000000 + iat_rva
        idx = 0
        while True:
            entry = struct.unpack_from('<I', dll, curr_ilt + idx*4)[0]
            if entry == 0: break
            if not (entry & 0x80000000): # by name
                hint_raw = rva2raw(entry)
                func_name = dll[hint_raw+2:dll.find(b'\x00', hint_raw+2)].decode('latin1')
                if func_name == 'send':
                    iat_send_va = curr_iat_va + idx*4
                    print(f"  send found at IAT VA: {hex(iat_send_va)}")
            idx += 1
    imp_off += 20

# Now find all calls in .text to iat_send_va (opcode FF 15 <iat_send_va>)
if iat_send_va:
    pattern = b'\xff\x15' + struct.pack('<I', iat_send_va)
    calls = []
    idx = 0
    while True:
        pos = dll.find(pattern, idx)
        if pos == -1: break
        calls.append(pos)
        idx = pos + 1
    print(f"Found {len(calls)} calls to send() in GameClient.dll:")
    for c in calls:
        va_call = 0x10001000 + (c - 0x400)
        print(f"  Raw: {hex(c)} (VA: {hex(va_call)})")
