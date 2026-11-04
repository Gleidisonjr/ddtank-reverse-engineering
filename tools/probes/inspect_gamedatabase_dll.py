import re, struct

with open(r'targets/district-187/client-rebirth/GameDatabase.dll', 'rb') as f:
    data = f.read()

# find all ASCII and UTF-16 strings
strings = re.findall(rb'[a-zA-Z0-9_\-\.:/\\%]{3,}', data)
print(f"=== GameDatabase.dll strings ({len(strings)}) ===")
for s in strings:
    s_dec = s.decode('latin1')
    if any(k in s_dec.lower() for k in ['ip', 'port', 'hook', 'patch', 'server', 'connect', 'gs_', 'cvar', 'launcher', 'cfg']):
        print(' ', s_dec)
