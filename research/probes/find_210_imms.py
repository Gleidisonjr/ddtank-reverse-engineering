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

text_s = pe.sections[0]
t_start = text_s.PointerToRawData
t_end = t_start + text_s.SizeOfRawData

# Look for ANY 0x2101xx or 0x2102xx or 0x1101xx immediate in .text
for off in range(t_start, t_end - 4):
    val = struct.unpack_from("<I", data, off)[0]
    if (val & 0xFFFF00) in (0x110100, 0x210100, 0x210200, 0x220100):
        print(f"Imm 0x{val:06x} at VA 0x{raw_to_va(off):08x} (opcode prev={data[off-1]:02x})")
