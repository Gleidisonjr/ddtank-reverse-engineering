import zlib

with open('projects/ddtank-server/www/flash/Loading.swf', 'rb') as f:
    data = f.read()

body = zlib.decompress(data[8:])

# Let's search for all pushstring instructions in the ABC bytecode (offsets 280000..314000)
# Look around 288000
chunk = body[287000:292000]

# Let's extract all readable ASCII strings of length >= 3 in this chunk
import re
matches = re.finditer(rb'[\x20-\x7e]{3,}', chunk)
for m in matches:
    print(f"Offset {287000+m.start()}: {m.group().decode('ascii')}")
