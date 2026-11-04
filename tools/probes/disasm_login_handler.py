import capstone

with open(r'targets/district-187/client-rebirth/Game/GameClient.dll', 'rb') as f:
    dll = f.read()

# 0x100d74a0
# .text starts at raw 0x400, VA 0x10001000
# Offset = 0x400 + (0x100d74a0 - 0x10001000) = 0x400 + 0xd64a0 = 0xd68a0
off = 0xd68a0
va = 0x100d74a0

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
for ins in md.disasm(dll[off:off+300], va):
    print(f"0x{ins.address:08x}: {ins.mnemonic:<8} {ins.op_str}")
