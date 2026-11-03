import struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
sys.stdout.reconfigure(encoding='utf-8')

with open(r"targets\district-187\client-rebirth\Game\GameClient.dll", "rb") as f:
    data = f.read()

# Find xrefs to 0x10486f4c, 0x10486900, 0x10486f18
for target_va in [0x10486f4c, 0x10486900, 0x104868de, 0x10486b43]:
    target_bytes = struct.pack("<I", target_va)
    idx = 0
    while True:
        idx = data.find(target_bytes, idx)
        if idx == -1:
            break
        print(f"Xref to 0x{target_va:08x} at file offset 0x{idx:x} (VA 0x{0x10000000+idx:08x})")
        idx += 1

md = Cs(CS_ARCH_X86, CS_MODE_32)
def disasm_range(start_off, length):
    print(f"\n=== Disassembly at VA 0x{0x10000000+start_off:08x} ===")
    for insn in md.disasm(data[start_off:start_off+length], 0x10000000 + start_off):
        comment = ""
        # check if operand has a VA inside rdata
        for word_off in range(len(insn.bytes) - 3):
            val = struct.unpack_from("<I", insn.bytes, word_off)[0]
            if 0x10460000 <= val <= 0x10510000:
                s_off = val - 0x10000000
                end = data.find(b"\x00", s_off)
                if end != -1 and 0 < end - s_off < 120:
                    s = data[s_off:end].decode("cp949", errors="replace")
                    if s.isprintable():
                        comment += f' ; "{s}"'
        print(f"0x{insn.address:08x}: {insn.mnemonic:<8} {insn.op_str}{comment}")

# Let's also check strings around 0x486800 - 0x487200
print("\n=== Strings in 0x486800 - 0x487500 ===")
cur = 0x486800
while cur < 0x487500:
    end = data.find(b"\x00", cur)
    if end == -1:
        break
    if end > cur:
        s = data[cur:end].decode("cp949", errors="replace")
        if len(s) > 2:
            print(f"0x{0x10000000+cur:08x}: {repr(s)}")
    cur = end + 1
