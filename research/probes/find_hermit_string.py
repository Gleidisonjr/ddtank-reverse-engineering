with open(r'targets/district-187/client-rebirth/TheRaw.exe', 'rb') as f:
    exe = f.read()

pos = exe.find(b'HermitClientLog')
while pos != -1:
    print("Found in TheRaw at raw:", hex(pos))
    print(" ", exe[max(0, pos-40):pos+80])
    pos = exe.find(b'HermitClientLog', pos+1)
