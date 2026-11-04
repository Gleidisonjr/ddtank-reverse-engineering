import capstone

with open(r'targets\district-187\client\S2\TheRaw.exe', 'rb') as f:
    data = f.read()

start_va = 0x0041693D
start_off = 0x0001693D - 0x1000 + 0x400
code = data[start_off : start_off + 0x100]

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
for i in md.disasm(code, start_va):
    print(f"0x{i.address:08X}: {i.mnemonic:<8} {i.op_str}")
