import zlib

with open('projects/ddtank-server/www/flash/Loading.swf', 'rb') as f:
    data = f.read()

body = zlib.decompress(data[8:])

abc_pos = body.find(b'Loading\x00')
abc_data = body[abc_pos+8:]

# Let's find REQUEST_PATH in abc_data
pos = abc_data.find(b'REQUEST_PATH')
print("REQUEST_PATH in abc_data:", pos)

# Find references to string index of REQUEST_PATH
# In earlier script, string count was 296
# Let's search for string 'REQUEST_PATH'
# string index: let's get exact index
strings = []
p = abc_data.find(b'\x01')
# Let's search bytes of REQUEST_PATH
rp_idx = 132 # let's check
for sidx in range(120, 140):
    needle = bytes([0x2C, sidx]) if sidx < 128 else bytes([0x2C, (sidx & 0x7F) | 0x80, sidx >> 7])
    matches = [i for i in range(len(abc_data)) if abc_data.startswith(needle, i)]
    if matches:
        print(f"String {sidx} at {matches}")

# Let's search for method body around offset 291000..291700
print("Disassembling 291400..291750:")
chunk = abc_data[291400:291750]
for i in range(0, len(chunk), 16):
    print(chunk[i:i+16].hex(' '))
