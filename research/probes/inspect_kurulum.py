import re

with open(r'targets/district-187/S2RebirthKurulum.exe', 'rb') as f:
    data = f.read()

# Let's inspect all strings in the #Strings or #US metadata stream
# Find 'BSJB' signature of .NET metadata
bsjb = data.find(b'BSJB')
print("BSJB at:", hex(bsjb))

# Find any strings containing .mdcreative or manifest or S2
for match in re.finditer(rb'([a-zA-Z0-9_\-\.:/]{4,})', data):
    s = match.group(1).decode('latin1', errors='ignore')
    if any(k in s.lower() for k in ['manifest', 'mdcreative', 'rebirth', 'download', 'kurulum', 's2']):
        print(s)
