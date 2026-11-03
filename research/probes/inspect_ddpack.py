import struct

with open(r"targets\dd-classico\extracted\app\resources\launcher.pack", "rb") as f:
    data = f.read()

magic = data[:8]
salt = data[8:24]
count = struct.unpack("<I", data[24:28])[0]
print(f"Magic: {magic}, Salt: {salt.hex()}, Count: {count}")

# Let's search for filenames in the pack data
known_names = [b"main.js", b"preload-main.js", b"preload-stopwatch.js", b"preload-webview.js", b"updater.js"]
for name in known_names:
    idx = 0
    while True:
        idx = data.find(name, idx)
        if idx == -1:
            break
        print(f"Found {name.decode()} at offset 0x{idx:x} ({idx})")
        # Check what precedes it (usually a uint16 length)
        pre_len = struct.unpack("<H", data[idx-2:idx])[0]
        print(f"  Preceding 2 bytes as uint16: {pre_len}")
        idx += len(name)
