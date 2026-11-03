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

md = Cs(CS_ARCH_X86, CS_MODE_32)

def disasm_va(va_start, length, label="", stop_on_ret=False):
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
        if stop_on_ret and insn.mnemonic == "ret":
            break

# 1. Disassemble the rest of 0x10032f30 (0x210121)
disasm_va(0x10032fa0, 0x300, "Rest of 0x210121 (0x10032fa0)", stop_on_ret=False)

# 2. Disassemble 0x1004b8a0 (SetFlashState / OpenMainScreen)
disasm_va(0x1004b8a0, 0x350, "SetFlashState 0x1004b8a0", stop_on_ret=True)

# 3. Find all callers of 0x1004b8a0 in .text!
text_s = pe.sections[0]
t_start = text_s.PointerToRawData
t_end = t_start + text_s.SizeOfRawData
print("\n=== All Callers of 0x1004b8a0 (SetFlashState) ===")
for off in range(t_start, t_end - 5):
    b = data[off]
    if b in (0xE8, 0xE9):
        rel = struct.unpack_from("<i", data, off + 1)[0]
        cur_va = raw_to_va(off)
        if (cur_va + 5 + rel) & 0xFFFFFFFF == 0x1004b8a0:
            # print 4 instructions before the call to see what state is pushed!
            prev_raw = off - 16
            insns = list(md.disasm(data[prev_raw:off+5], cur_va - 16))
            ctx = " | ".join(f"{i.mnemonic} {i.op_str}" for i in insns[-3:])
            print(f"  {'CALL' if b==0xE8 else 'JMP '} @ 0x{cur_va:08x}: {ctx}")
