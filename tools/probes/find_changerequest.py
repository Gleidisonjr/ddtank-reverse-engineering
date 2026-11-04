import zlib

with open('projects/ddtank-server/www/flash/Loading.swf', 'rb') as f:
    data = f.read()

body = zlib.decompress(data[8:])
abc_pos = body.find(b'Loading\x00')
abc_data = body[abc_pos+8:]

# Search for changeRequestMethod in abc_data
pos = abc_data.find(b'changeRequestMethod')
print("changeRequestMethod string in abc_data:", pos)

# Find where changeRequestMethod method body is
# Method name was string index: let's search for bytes around pos
# In strings:
idx = 0
for i in range(len(abc_data)):
    if b'changeRequestMethod' in abc_data[i:i+30]:
        print(f"Match at {i}: {abc_data[i:i+40]}")
