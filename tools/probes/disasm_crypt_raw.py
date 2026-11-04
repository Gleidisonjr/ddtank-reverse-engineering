import capstone

with open(r'targets/district-187/client-rebirth/TheRaw.exe', 'rb') as f:
    exe = f.read()

# .text raw is 0x400, VA 0x401000
def va2raw(va):
    return 0x400 + (va - 0x401000)

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

print("=== Disassembly around 0x5baba0 (CryptImportKey & CryptEncrypt) ===")
raw1 = va2raw(0x5aba50)
for ins in md.disasm(exe[raw1:raw1+200], 0x5aba50):
    print(f"0x{ins.address:08x}: {ins.mnemonic:<8} {ins.op_str}")

print("\n=== Disassembly around 0x5b4aea (CryptDeriveKey & CryptDecrypt) ===")
raw2 = va2raw(0x5b4a00)
for ins in md.disasm(exe[raw2:raw2+250], 0x5b4a00):
    print(f"0x{ins.address:08x}: {ins.mnemonic:<8} {ins.op_str}")
