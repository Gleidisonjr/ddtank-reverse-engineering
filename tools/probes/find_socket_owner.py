import os, glob

for path in glob.glob(r'targets/district-187/client-rebirth/*.dll') + \
            glob.glob(r'targets/district-187/client-rebirth/*.exe') + \
            glob.glob(r'targets/district-187/client-rebirth/Game/*.dll'):
    with open(path, 'rb') as f: data = f.read()
    if b'WSAStartup' in data or b'connect\x00' in data:
        print(f"Socket library in: {os.path.basename(path)}")
