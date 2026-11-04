import capstone
import struct

with open(r'targets\district-187\client\S2\Game\GameClient.dll', 'rb') as f:
    data = f.read()

# 0x23A0A7 file offset is RVA 0x0023ACA7, VA 0x1023ACA7
# Let's disassemble from 0x23A000 to 0x23A200
file_start = 0x23A000
code_bytes = data[file_start : file_start + 0x200]
start_va = 0x10000000 + 0x00001000 + (file_start - 0x400)

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
for insn in md.disasm(code_bytes, start_va):
    print(f"0x{insn.address:08X}:  {insn.mnemonic:<8} {insn.op_str}")
