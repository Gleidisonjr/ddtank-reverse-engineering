import capstone

with open(r'targets/district-187/client-rebirth/Game/GameClient.dll', 'rb') as f:
    dll = f.read()

# 0x10057180
# .text starts at raw 0x400, VA 0x10001000
# Offset = 0x400 + (0x10057180 - 0x10001000) = 0x400 + 0x56180 = 0x56580
off = 0x56580
va = 0x10057180

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
for ins in md.disasm(dll[off:off+350], va):
    print(f"0x{ins.address:08x}: {ins.mnemonic:<8} {ins.op_str}")
