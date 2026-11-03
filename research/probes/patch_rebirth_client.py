import os, sys

target_dll = r'targets/district-187/client-rebirth/Game/GameClient.dll'
backup_dll = r'targets/district-187/client-rebirth/Game/GameClient.dll.original'

if not os.path.exists(backup_dll):
    with open(target_dll, 'rb') as f_in, open(backup_dll, 'wb') as f_out:
        f_out.write(f_in.read())
    print(f"[+] Created backup: {backup_dll}")

with open(target_dll, 'rb') as f:
    data = bytearray(f.read())

offset = 0xd6d64
patch_code = bytes.fromhex('bf5cc84910c744246c00803b46' + '90' * 66)
assert len(patch_code) == 79, f"Invalid patch length: {len(patch_code)}"

print(f"Current bytes at {hex(offset)}:")
print(" ", data[offset:offset+20].hex())

data[offset:offset+len(patch_code)] = patch_code

with open(target_dll, 'wb') as f:
    f.write(data)

print(f"[+] Successfully patched GameClient.dll at {hex(offset)} (79 bytes) to hardwire 127.0.0.1:12000!")
