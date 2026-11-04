import zlib

with open('projects/ddtank-server/www/flash/Loading.swf', 'rb') as f:
    data = f.read()

body = zlib.decompress(data[8:])

# Find DoABC
pos = body.find(b'LoginSelectList.ashx')
print("LoginSelectList.ashx string offset in body:", pos)

# Let's find the method body around pos
# In ABC data:
abc_pos = body.find(b'Loading\x00')
abc_data = body[abc_pos+8:]

idx = abc_data.find(b'\xaa\x01') # string index 170
print("Offsets of string 170 in abc_data:", [i for i in range(len(abc_data)) if abc_data.startswith(b'\x2c\xaa\x01', i)])

# Let's disassemble the method that contains 0x2c 0xaa 0x01
off = abc_data.find(b'\x2c\xaa\x01')
start = max(0, off - 60)
end = min(len(abc_data), off + 150)
code = abc_data[start:end]
print("Code bytes:")
for i in range(0, len(code), 16):
    print(code[i:i+16].hex(' '))
