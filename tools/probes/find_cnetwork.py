import struct, capstone

with open(r'targets/district-187/client-rebirth/TheRaw.exe', 'rb') as f:
    exe = f.read()

# 'CNetWork\x00' is at raw 0x3e7d5c
# In TheRaw.exe: .rdata is VA 0x76b000 or similar
# Let's find section for 0x3e7d5c
import find_crypto_iat
# rva for raw 0x3e7d5c
for va, raw, sz in find_crypto_iat.sections:
    if raw <= 0x3e7d5c < raw + sz:
        str_va = 0x400000 + va + (0x3e7d5c - raw)
        print("CNetWork string VA:", hex(str_va))
        pat = struct.pack('<I', str_va)
        idx = 0
        while True:
            p = exe.find(pat, idx)
            if p == -1: break
            ref_va = 0x400000 + find_crypto_iat.sections[0][0] + (p - find_crypto_iat.sections[0][1])
            print(f"  Referenced at VA: {hex(ref_va)} (raw: {hex(p)})")
            idx = p + 1
