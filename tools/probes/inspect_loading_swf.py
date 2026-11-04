import zlib
import struct
import os

swf_path = 'projects/ddtank-server/www/flash/Loading.swf'
with open(swf_path, 'rb') as f:
    data = f.read()

sig = data[:3]
ver = data[3]
file_len = struct.unpack('<I', data[4:8])[0]

if sig == b'CWS':
    body = zlib.decompress(data[8:])
elif sig == b'FWS':
    body = data[8:]
elif sig == b'ZWS':
    import lzma
    body = lzma.decompress(data[8:])

print(f"Sig: {sig}, Version: {ver}, Uncompressed Len: {len(body)}")

# Search for strings in body
import re
strings = re.findall(rb'[\x20-\x7e]{4,}', body)
print(f"Found {len(strings)} ASCII strings in Loading.swf")

# Print strings that look like XML, URLs, class names, or flashvars
interesting = []
for s in strings:
    s_str = s.decode('ascii', errors='ignore')
    if any(k in s_str.lower() for k in ['xml', 'swf', 'flashvars', 'config', 'user', 'key', 'site', 'request', 'load', 'login', '2.swf', 'ddt_loading']):
        interesting.append(s_str)

print("Interesting strings in Loading.swf:")
for s in set(interesting):
    print("  ", s)
