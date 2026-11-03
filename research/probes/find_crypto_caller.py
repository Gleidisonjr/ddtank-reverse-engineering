import struct

with open(r'targets/district-187/client-rebirth/TheRaw.exe', 'rb') as f:
    exe = f.read()

target_va = 0x5b4a00
# search for call target_va (rel32 = target_va - (call_va + 5))
# or search in .text
calls = []
for i in range(len(exe) - 5):
    if exe[i] == 0xe8: # call rel32
        rel = struct.unpack_from('<i', exe, i+1)[0]
        cur_va = 0x401000 + (i - 0x400)
        dest_va = cur_va + 5 + rel
        if dest_va == target_va:
            calls.append(cur_va)

print(f"Calls to 0x5b4a00: {[hex(c) for c in calls]}")
