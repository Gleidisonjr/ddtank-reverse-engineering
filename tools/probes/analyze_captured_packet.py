with open(r'targets/district-187/traffic/20261102_194718_031248_TCP.bin', 'rb') as f:
    data = f.read()

print("Payload len:", len(data))
print("Hex:", data.hex())

# Let's inspect GameClient.dll around send() or WSASend()
import re

with open(r'targets/district-187/client-rebirth/Game/GameClient.dll', 'rb') as f:
    dll = f.read()

# Look for send calls or packet encrypt
print("Searching for crypto/handshake in GameClient...")
terms = [b'Seed', b'Crypt', b'Encrypt', b'Key', b'Handshake', b'Blowfish', b'AES', b'DES', b'RC4', b'TEA']
for t in terms:
    matches = set(re.findall(rb'[a-zA-Z0-9_]*' + t + rb'[a-zA-Z0-9_]*', dll))
    valid = [m.decode('latin1') for m in matches if 3 <= len(m) < 30]
    if valid:
        print(f"  {t.decode()}: {valid[:8]}")
