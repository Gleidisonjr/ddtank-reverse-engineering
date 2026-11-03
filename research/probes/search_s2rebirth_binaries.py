import re

with open(r'targets/district-187/client-rebirth/D3DX9_43.dll', 'rb') as f:
    data = f.read()

strings = re.findall(rb'[a-zA-Z0-9_\-\.:/\\]{4,}', data)
print("=== D3DX9_43.dll Strings ===")
for s in strings:
    s_dec = s.decode('latin1')
    if any(k in s_dec.lower() for k in ['apex', 'hook', 'load', 'proxy', 'raw', 's2', 'ip', 'server']):
        print(f"  {s_dec}")
