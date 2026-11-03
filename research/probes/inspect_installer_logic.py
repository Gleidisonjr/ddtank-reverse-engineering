with open(r'targets/district-187/S2RebirthKurulum.exe', 'rb') as f:
    data = f.read()

import re
# Search for string literal containing '/' in #US stream
# In .NET #US stream, let's dump all strings that have '/' or '.' or '{'
u16 = re.findall(rb'(?:[\x20-\x7e]\x00){1,}', data[0xa8000:0xb0000])
for s in u16:
    s_dec = s.decode('utf-16le', errors='ignore')
    if '/' in s_dec or '{' in s_dec or 'http' in s_dec:
        print(repr(s_dec))
