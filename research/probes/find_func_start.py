import capstone

with open(r'targets/district-187/client-rebirth/TheRaw.exe', 'rb') as f:
    exe = f.read()

def va2raw(va):
    return 0x400 + (va - 0x401000)

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
# search backward from 0x5b4980
for start in range(0x5b4980, 0x5b4800, -16):
    raw = va2raw(start)
    if exe[raw] in (0x55, 0x83, 0x53): # potential prologue
        for ins in md.disasm(exe[raw:raw+30], start):
            if ins.mnemonic in ('push', 'sub') and 'ebp' in ins.op_str:
                print(f"Possible func at VA: {hex(ins.address)}")
