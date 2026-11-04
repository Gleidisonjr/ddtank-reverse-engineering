import zlib

with open('projects/ddtank-server/www/flash/Loading.swf', 'rb') as f:
    data = f.read()

body = zlib.decompress(data[8:])
abc_pos = body.find(b'Loading\x00')
abc_data = body[abc_pos+8:]

# Method bodies in ABC have a header: method, max_stack, nlocals, init_scope, max_scope, code_len...
# In disasm_config_complete.py we had:
# 66 46 59 48 24 00 66 0c 66 54 66 07 2c 1b ab 96 4f 25 03
# Let's search for this byte sequence:
sig = bytes.fromhex("66 46 59 48 24 00 66 0c")
pos = abc_data.find(sig)
print("Signature found at:", pos)

# Let's print 100 bytes BEFORE pos
start = max(0, pos - 150)
chunk = abc_data[start:pos+50]
for i in range(0, len(chunk), 16):
    print(chunk[i:i+16].hex(' '))
