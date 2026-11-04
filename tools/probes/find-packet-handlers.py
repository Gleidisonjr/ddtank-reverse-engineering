import capstone
import struct

with open(r'targets\district-187\client\S2\Game\GameClient.dll', 'rb') as f:
    data = f.read()

# Search for cmp ..., 0x62 or cmp ..., 0x63 or case 0x62 / 0x63
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

for off in range(0x400, len(data) - 100, 1000):
    chunk = data[off:off+1000]
    for insn in md.disasm(chunk, 0x10000000 + 0x1000 + (off - 0x400)):
        if insn.mnemonic in ['cmp', 'sub'] and ('0x62' in insn.op_str or '0x63' in insn.op_str):
            print(f"0x{insn.address:08X}: {insn.mnemonic:<8} {insn.op_str}")
