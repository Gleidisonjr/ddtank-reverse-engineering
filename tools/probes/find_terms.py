import zlib

with open('projects/ddtank-server/www/flash/Loading.swf', 'rb') as f:
    data = f.read()

body = zlib.decompress(data[8:])

# Find the offset of __onConfigLoadComplete
target = b'__onConfigLoadComplete'
idx = body.find(target)
print("Index of __onConfigLoadComplete:", idx)

# Let's search for references to this index in the file
# Or search for the method body where USEMD5 or FLASHSITE is used
for term in [b'FLASHSITE', b'USEMD5', b'USE_MD5', b'LoginSelectList', b'DDT_Loading.swf', b'loadSelectList']:
    p = 0
    while True:
        pos = body.find(term, p)
        if pos == -1:
            break
        print(f"Term '{term.decode()}' at {pos}")
        # print 60 bytes around pos
        chunk = body[max(0, pos-20):pos+len(term)+40]
        # print printable ASCII
        print("   Ascii:", "".join(chr(c) if 32 <= c <= 126 else "." for c in chunk))
        p = pos + len(term)
