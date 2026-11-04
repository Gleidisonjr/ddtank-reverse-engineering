import pefile, struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
sys.stdout.reconfigure(encoding='utf-8')

pe = pefile.PE(r"targets\district-187\client-rebirth\Game\GameClient.dll", fast_load=True)
image_base = pe.OPTIONAL_HEADER.ImageBase
with open(r"targets\district-187\client-rebirth\Game\GameClient.dll", "rb") as f:
    data = f.read()

def va_to_raw(va):
    rva = va - image_base
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (rva - s.VirtualAddress)
    return 0

def raw_to_va(raw):
    for s in pe.sections:
        if s.PointerToRawData <= raw < s.PointerToRawData + s.SizeOfRawData:
            return image_base + s.VirtualAddress + (raw - s.PointerToRawData)
    return 0

# Dump vtables from VA 0x1049de00 to 0x1049e400
for va in range(0x1049df30, 0x1049e200, 12):
    raw = va_to_raw(va)
    f0, f1, f2 = struct.unpack_from("<III", data, raw)
    # Search for references to this vtable VA in .text or .rdata
    refs = []
    for cand_va in (va, va - 4):
        b = struct.pack("<I", cand_va)
        idx = 0
        while True:
            idx = data.find(b, idx)
            if idx == -1:
                break
            refs.append(f"0x{raw_to_va(idx):08x}")
            idx += 1
    print(f"Vtable 0x{va:08x}: [0]=0x{f0:08x}, [4]=0x{f1:08x}, [8]=0x{f2:08x} | Refs={refs}")
