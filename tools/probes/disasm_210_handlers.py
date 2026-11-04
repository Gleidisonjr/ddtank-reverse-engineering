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

md = Cs(CS_ARCH_X86, CS_MODE_32)

def disasm_va(va_start, length, label=""):
    raw_start = va_to_raw(va_start)
    print(f"\n=== {label} @ VA 0x{va_start:08x} (raw 0x{raw_start:x}) ===")
    for insn in md.disasm(data[raw_start:raw_start+length], va_start):
        comment = ""
        for word_off in range(len(insn.bytes) - 3):
            val = struct.unpack_from("<I", insn.bytes, word_off)[0]
            if 0x10482000 <= val <= 0x104ebc00:
                s_off = va_to_raw(val)
                end = data.find(b"\x00", s_off)
                if end != -1 and 0 < end - s_off < 120:
                    s = data[s_off:end].decode("cp949", errors="replace")
                    if s.isprintable():
                        comment += f' ; "{s}"'
        print(f"0x{insn.address:08x}: {insn.mnemonic:<8} {insn.op_str}{comment}")
        if insn.mnemonic == "ret":
            break

# Disassemble .s2zm, .s2fk, .s2mk, .s2fp, .s2kl
for s in pe.sections:
    name = s.Name.decode('latin1').strip('\x00')
    if name.startswith('.s2'):
        va = image_base + s.VirtualAddress
        disasm_va(va, s.SizeOfRawData, f"Section {name}")

# Disassemble handlers for 0x110125, 0x210141, 0x210111, 0x210113, 0x210121, 0x210202, 0x210103, 0x210105, 0x210123, 0x210131, 0x210122, 0x210222, 0x210151, 0x210152
handlers = [
    (0x10030c90, "0x110125"),
    (0x10030cc0, "0x210141"),
    (0x10031000, "0x210111"),
    (0x100312b0, "0x210113"),
    (0x10032f30, "0x210121"),
    (0x10031bc0, "0x210202 (SN_LockEnd)"),
    (0x10031140, "0x210103"),
    (0x10031110, "0x210105"),
    (0x10031200, "0x210123"),
    (0x10030340, "0x210131"),
    (0x10030dc0, "0x210122"),
    (0x10032cc0, "0x210222"),
    (0x100334a0, "0x210151"),
    (0x10033520, "0x210152"),
]
for va, name in handlers:
    disasm_va(va, 0x250, f"Handler {name}")
