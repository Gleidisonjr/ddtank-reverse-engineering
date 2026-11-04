import zlib

with open('projects/ddtank-server/www/flash/Loading.swf', 'rb') as f:
    data = f.read()

body = zlib.decompress(data[8:])

# Let's search for "USE_MD5" or "USEMD5" in the method bodies
# Find all occurrences of "USE_MD5"
idx = 0
while True:
    pos = body.find(b'USE_MD5', idx)
    if pos == -1:
        break
    print(f"USE_MD5 at {pos}")
    idx = pos + 7
