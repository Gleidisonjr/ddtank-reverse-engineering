import struct

with open(r'targets/district-187/traffic/20261102_200716_921288_TCP.bin', 'rb') as f:
    data = f.read()

print("Bytes:", data.hex())
print("Length:", len(data))

# Try various struct formats:
for off in range(5):
    if len(data) >= off + 16:
        print(f"--- Offset {off} ---")
        try:
            # Format: size (uint16), ...
            u16_0 = struct.unpack_from('<H', data, off)[0]
            u16_1 = struct.unpack_from('<H', data, off+2)[0]
            u32_0 = struct.unpack_from('<I', data, off)[0]
            u32_1 = struct.unpack_from('<I', data, off+4)[0]
            u32_2 = struct.unpack_from('<I', data, off+8)[0]
            u32_3 = struct.unpack_from('<I', data, off+12)[0]
            print(f"  u16: {hex(u16_0)}, {hex(u16_1)}")
            print(f"  u32: {hex(u32_0)}, {hex(u32_1)}, {hex(u32_2)}, {hex(u32_3)}")
        except Exception as e:
            print("  error:", e)
