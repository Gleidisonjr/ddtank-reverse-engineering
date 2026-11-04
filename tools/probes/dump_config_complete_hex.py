import zlib

with open('projects/ddtank-server/www/flash/Loading.swf', 'rb') as f:
    data = f.read()

body = zlib.decompress(data[8:])
abc_pos = body.find(b'Loading\x00')
abc_data = body[abc_pos+8:]

# In find_exact_code.py, body_offset was 5115
# Method __onConfigLoadComplete body started at 5115 + 46 (which was 5161)
code = abc_data[5161:5360]

# Let's print each byte and its offset
for i in range(0, len(code), 16):
    line = code[i:i+16]
    hex_str = " ".join(f"{b:02x}" for b in line)
    print(f"{i:4d}: {hex_str}")
