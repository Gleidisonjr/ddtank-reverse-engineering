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
                vt_f0, vt_f1 = struct.unpack_from("<II", data, s_off)
                if 0x10001000 <= vt_f1 <= 0x10480000:
                    comment += f" ; Vtable([4]=0x{vt_f1:08x})"
        print(f"0x{insn.address:08x}: {insn.mnemonic:<8} {insn.op_str}{comment}")
        if stop_on_ret and insn.mnemonic == "ret":
            break

for name, vt_va in [("State 0 (ServerList)", 0x1049cabc), ("State 1 (ChannelList)", 0x104a2efc), ("State 2 (Lobby)", 0x1049e038)]:
    raw = va_to_raw(vt_va)
    fns = struct.unpack_from("<8I", data, raw)
    print(f"\n{name} Vtable @ 0x{vt_va:08x}: " + ", ".join(f"[{i*4}]=0x{f:08x}" for i, f in enumerate(fns)))
    for i in (2, 3, 4, 5):
        if 0x10001000 <= fns[i] <= 0x10480000:
            disasm_va(fns[i], 0x1c0, f"{name} vtable[{i*4}]", stop_on_ret=True)
