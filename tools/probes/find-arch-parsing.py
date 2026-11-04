with open(r'targets\district-187\client\S2\TheRaw.exe', 'rb') as f:
    data = f.read()

import re
matches = [m.start() for m in re.finditer(rb'-arch\b', data)]
for m in matches:
    print(f"Found '-arch' at 0x{m:06X}")
    chunk = data[m-50:m+150]
    for s in re.findall(rb'[\x20-\x7E]{3,}', chunk):
        print("  ", s.decode('latin1'))
