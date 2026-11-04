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

def disasm_va(va_start, length):
    raw_start = va_to_raw(va_start)
    print(f"\n=== Disassembly at VA 0x{va_start:08x} (raw 0x{raw_start:x}) ===")
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

# Find callers of 0x10051ed0 (EnterChannel) and 0x10051f60 (_Send_Login_Join)
for fn_va in [0x10051ed0, 0x10051f60, 0x10052f70, 0x100528b0]:
    print(f"\n--- Callers of 0x{fn_va:08x} ---")
    # scan .text for E8/E9 rel32
    text_s = pe.sections[0]
    text_raw = text_s.PointerToRawData
    text_va = image_base + text_s.VirtualAddress
    for off in range(text_raw, text_raw + text_s.SizeOfRawData - 5):
        b = data[off]
        if b in (0xE8, 0xE9):
            rel = struct.unpack_from("<i", data, off + 1)[0]
            cur_va = text_va + (off - text_raw)
            if (cur_va + 5 + rel) & 0xFFFFFFFF == fn_va:
                print(f"  {'CALL' if b==0xE8 else 'JMP'} from VA 0x{cur_va:08x}")

# Let's also check the packet table in .rdata!
# Earlier we found packet IDs 0x110102, 0x110112, 0x210101, 0x210102, etc.
# Let's dump ALL packet handlers in 0x11xxxx and 0x21xxxx and 0x22xxxx!
print("\n--- Packet Table Entries for 0x11xxxx, 0x21xxxx, 0x22xxxx ---")
rdata_s = pe.sections[1]
r_start = rdata_s.PointerToRawData
r_end = r_start + rdata_s.SizeOfRawData
for off in range(r_start, r_end - 8, 4):
    pkt_id, vtable_va = struct.unpack_from("<II", data, off)
    if (pkt_id & 0xFFF000) in (0x110000, 0x210000, 0x220000) and 0x10482000 <= vtable_va <= 0x104ebc00:
        vt_raw = va_to_raw(vtable_va)
        if vt_raw:
            fn1, fn2 = struct.unpack_from("<II", data, vt_raw)
            print(f"PktID 0x{pkt_id:06x} @ VA 0x{raw_to_va(off):08x} -> Vtable 0x{vtable_va:08x} -> [0]=0x{fn1:08x}, [4]=0x{fn2:08x}")
