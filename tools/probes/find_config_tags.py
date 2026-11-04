import zlib
import re

with open('projects/ddtank-server/www/flash/Loading.swf', 'rb') as f:
    data = f.read()

body = zlib.decompress(data[8:])

# Find all uppercase strings or tag names in Loading.swf
xml_tags = re.findall(rb'[A-Z0-9_]{3,}', body)
tags = set(t.decode('ascii', errors='ignore') for t in xml_tags)
print("Config/XML tags found in Loading.swf:")
for t in sorted(tags):
    if any(k in t for k in ['SITE', 'PATH', 'URL', 'FLASH', 'MD5', 'CONFIG', 'LOAD', 'USER', 'VERSION', 'REQUEST']):
        print("  ", t)
