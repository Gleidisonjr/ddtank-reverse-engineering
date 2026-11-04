import struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

with open(r"targets\district-187\client-rebirth\Game\GameClient.dll", "rb") as f:
    data = f.read()

# Find strings related to login and FLASH_STATE
for s in [b"FLASH_STATE::eLOGIN", b"_Send_Login_ID", b"OnServerConnected", b"OpenMainScreen", b"loginClick"]:
    idx = 0
    while True:
        idx = data.find(s, idx)
        if idx == -1:
            break
        End = data.find(b"\x00", idx)
        print(f"String @ 0x{0x10000000 + idx:08x} (off 0x{idx:x}): {data[idx:End].decode('cp949', errors='replace')}")
        idx += 1

# Find all strings starting with "FLASH_STATE::"
idx = 0
while True:
    idx = data.find(b"FLASH_STATE::", idx)
    if idx == -1:
        break
    End = data.find(b"\x00", idx)
    print(f"FLASH_STATE @ 0x{0x10000000 + idx:08x}: {data[idx:End].decode('cp949', errors='replace')}")
    idx += 1
