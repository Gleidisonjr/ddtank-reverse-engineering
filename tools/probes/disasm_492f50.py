import pefile, capstone

pe = pefile.PE(r'targets\district-187\client-rebirth\TheRaw.exe')
offset = pe.get_offset_from_rva(0x492f50 - 0x400000)
with open(r'targets\district-187\client-rebirth\TheRaw.exe', 'rb') as f:
    f.seek(offset)
    code = f.read(250)

cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
for i in cs.disasm(code, 0x492f50):
    print(f"0x{i.address:08x}: {i.mnemonic} {i.op_str}")
