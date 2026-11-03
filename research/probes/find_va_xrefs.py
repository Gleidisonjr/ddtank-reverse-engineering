import pefile, struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
sys.stdout.reconfigure(encoding='utf-8')

pe = pefile.PE(r"targets\district-187\client-rebirth\Game\GameClient.dll", fast_load=True)
image_base = pe.OPTIONAL_HEADER.ImageBase
print(f"ImageBase: 0x{image_base:08x}")
for s in pe.sections:
    print(f"Section {s.Name.decode('latin1').strip(chr(0)):<8} VA=0x{image_base+s.VirtualAddress:08x} Raw=0x{s.PointerToRawData:08x} Size=0x{s.SizeOfRawData:08x}")

with open(r"targets\district-187\client-rebirth\Game\GameClient.dll", "rb") as f:
    data = f.read()

def raw_to_va(raw):
    for s in pe.sections:
        if s.PointerToRawData <= raw < s.PointerToRawData + s.SizeOfRawData:
            return image_base + s.VirtualAddress + (raw - s.PointerToRawData)
    return 0

def va_to_raw(va):
    rva = va - image_base
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (rva - s.VirtualAddress)
    return 0

for s_pat in [b"FLASH_STATE::eLOGIN", b"FLASH_STATE::eSERVER - this->_Send_Login_Join", b"SceneChange.OpenMainScreen", b"CGameServerConnectMgr::EnterChannel"]:
    raw = data.find(s_pat)
    va = raw_to_va(raw)
    print(f"\nPattern {s_pat!r}: raw=0x{raw:x}, VA=0x{va:08x}")
    target_bytes = struct.pack("<I", va)
    idx = 0
    while True:
        idx = data.find(target_bytes, idx)
        if idx == -1:
            break
        print(f"  Xref at raw 0x{idx:x} (VA 0x{raw_to_va(idx):08x})")
        idx += 1
