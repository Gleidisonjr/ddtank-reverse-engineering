import zlib

with open('projects/ddtank-server/www/flash/Loading.swf', 'rb') as f:
    data = f.read()

body = zlib.decompress(data[8:])

# Look for strings containing @value or text() or child nodes
import re
# Look for XML attribute access in ABC: MultinameA or property names
strs = re.findall(rb'[\x20-\x7e]{2,}', body)
for s in strs:
    try:
        t = s.decode('ascii')
        if any(k in t for k in ['FLASHSITE', 'SITE', 'REQUEST_PATH', 'USE_MD5', 'MD5', 'config', 'value']):
            print("Found:", t)
    except:
        pass
