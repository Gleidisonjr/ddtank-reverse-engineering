import re

for path in [r'targets/district-187/client-rebirth/TheRaw.exe',
             r'targets/district-187/client-rebirth/Engine_Server.dll',
             r'targets/district-187/client-rebirth/Game/GameClient.dll']:
    with open(path, 'rb') as f: data = f.read()
    print(f"=== {path} ===")
    for term in [b'Encrypt', b'Decrypt', b'Cipher', b'Handshake', b'Key', b'Seed']:
        matches = set(re.findall(rb'[a-zA-Z0-9_]*' + term + rb'[a-zA-Z0-9_]*', data))
        valid = [m.decode('latin1') for m in matches if 3 <= len(m) < 30]
        if valid:
            print(f"  {term.decode()}: {valid[:8]}")
