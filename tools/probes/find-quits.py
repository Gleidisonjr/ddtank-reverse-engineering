import struct

with open(r'targets\district-187\client\S2\Game\GameClient.dll', 'rb') as f:
    data = f.read()

# Let's search for strings like "exit", "quit", "PostQuitMessage"
import re
for m in re.finditer(rb'PostQuitMessage', data):
    print("Found PostQuitMessage at offset:", hex(m.start()))

for m in re.finditer(rb'ExitProcess', data):
    print("Found ExitProcess at offset:", hex(m.start()))
