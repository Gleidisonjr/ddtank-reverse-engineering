import capstone

with open(r'targets/district-187/client-rebirth/Game/GameClient.dll', 'rb') as f:
    dll = f.read()

# 0x10132000
off = 0x400 + (0x10132000 - 0x10001000)
va = 0x10132000

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
for ins in md.disasm(dll[off:off+250], va):
    print(f"0x{ins.address:08x}: {ins.mnemonic:<8} {ins.op_str}")
