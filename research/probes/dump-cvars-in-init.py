import capstone
with open(r'targets\district-187\client\S2\Game\GameClient.dll', 'rb') as f:
    data = f.read()

code = data[0x23A000 : 0x23B000]
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
for i in md.disasm(code, 0x1023AC00):
    if i.mnemonic == 'push' and i.op_str.startswith('0x104'):
        try:
            addr = int(i.op_str, 16)
            off = addr - 0x10000000 - 0x00482000 + 0x00480600
            s = ''
            while off < len(data) and data[off] != 0 and 32 <= data[off] < 127:
                s += chr(data[off])
                off += 1
            if len(s) >= 2:
                print(f"0x{i.address:08X}: push {i.op_str} -> \"{s}\"")
        except Exception:
            pass
