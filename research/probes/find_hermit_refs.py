import struct

with open(r'targets/district-187/client-rebirth/TheRaw.exe', 'rb') as f:
    exe = f.read()

import find_crypto_iat
str_raw = exe.find(b'%d_%s\x00\x00\x00HermitClientLog')
print(f"Format string at raw: {hex(str_raw)}")

# Search for any references to nearby offsets in .text
for off in range(str_raw - 32, str_raw + 32, 4):
    for va, raw, sz in find_crypto_iat.sections:
        if raw <= off < raw + sz:
            cur_va = 0x400000 + va + (off - raw)
            p = exe.find(struct.pack('<I', cur_va))
            if p != -1:
                call_va = 0x400000 + find_crypto_iat.sections[0][0] + (p - find_crypto_iat.sections[0][1])
                print(f"  String VA {hex(cur_va)} referenced at VA: {hex(call_va)} (raw: {hex(p)})")
