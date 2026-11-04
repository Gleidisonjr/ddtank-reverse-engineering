import zlib
import struct
import re

with open('projects/ddtank-server/www/flash/2.swf', 'rb') as f:
    data = f.read()

sig = data[:3]
if sig == b'CWS':
    body = zlib.decompress(data[8:])
elif sig == b'FWS':
    body = data[8:]

print(f"2.swf body size: {len(body)} bytes")

# Search for flashvars / loaderInfo / parameters in 2.swf
strs = re.findall(rb'[\x20-\x7e]{4,}', body)
print(f"Total ASCII strings in 2.swf: {len(strs)}")

params = []
for s in strs:
    t = s.decode('ascii', errors='ignore')
    if any(k in t.lower() for k in ['flashvars', 'parameters', 'user', 'config.xml', 'crossdomain', '127.0.0.1']):
        if len(t) < 50:
            params.append(t)

print("Sample matching strings in 2.swf:")
for p in set(params[:40]):
    print(" ", p)
