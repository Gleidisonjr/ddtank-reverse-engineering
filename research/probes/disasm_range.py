import capstone

with open(r'targets/district-187/client-rebirth/TheRaw.exe', 'rb') as f:
    exe = f.read()

def va2raw(va):
    return 0x400 + (va - 0x401000)

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
raw = va2raw(0x5b4850)
for ins in md.disasm(exe[raw:raw+350], 0x5b4850):
    print(f"0x{ins.address:08x}: {ins.mnemonic:<8} {ins.op_str}")
