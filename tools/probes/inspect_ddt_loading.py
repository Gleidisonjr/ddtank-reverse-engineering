import zlib
import re

with open('projects/ddtank-server/www/flash/DDT_Loading.swf', 'rb') as f:
    data = f.read()

sig = data[:3]
if sig == b'CWS':
    body = zlib.decompress(data[8:])
elif sig == b'FWS':
    body = data[8:]

print(f"DDT_Loading.swf Uncompressed: {len(body)} bytes")

# Search for strings
strs = re.findall(rb'[\x20-\x7e]{4,}', body)
print(f"Found {len(strs)} strings in DDT_Loading.swf")
for s in strs:
    t = s.decode('ascii', errors='ignore')
    if any(k in t.lower() for k in ['2.png', '2.swf', 'load', 'config', 'user', 'flashsite']):
        print("  DDT_Loading:", t)
