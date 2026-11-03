with open(r'targets\district-187\client\S2\LauncherApp.exe', 'rb') as f:
    data = f.read()

import re
# Find #US stream
us_idx = data.find(b'#US\0')
print('#US stream marker at:', hex(us_idx))

# Dump all UTF-16 strings
strings = re.findall(rb'(?:[\x20-\x7E]\x00){3,}', data)
print(f"Total UTF-16 strings: {len(strings)}")
for s in strings:
    decoded = s.decode('utf-16le', errors='ignore')
    if any(k in decoded.lower() for k in ['theraw', 'arg', 'http', 'cmd', 'launch', 'server', 'port', 'process', 'start', 'exe']):
        print(f"  {decoded}")
