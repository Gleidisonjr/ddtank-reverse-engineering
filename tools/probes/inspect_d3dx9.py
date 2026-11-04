import capstone

with open(r'targets/district-187/client-rebirth/D3DX9_43.dll', 'rb') as f:
    dll = f.read()

# RVA is 0x4094
entry_raw = 0x3300 + (0x4094 - 0x3f00)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
for ins in md.disasm(dll[entry_raw:entry_raw+200], 0x10004094):
    print(f"0x{ins.address:08x}: {ins.mnemonic:<8} {ins.op_str}")
