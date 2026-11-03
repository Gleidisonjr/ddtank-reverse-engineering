import struct, capstone

with open(r'targets/district-187/client-rebirth/TheRaw.exe', 'rb') as f:
    exe = f.read()

# Find CryptEncrypt and CryptDecrypt in TheRaw.exe
import re
for name in [b'CryptEncrypt', b'CryptDecrypt', b'CryptImportKey', b'CryptCreateHash']:
    pos = exe.find(name)
    print(f"String '{name.decode()}' at raw: {hex(pos) if pos != -1 else 'None'}")
