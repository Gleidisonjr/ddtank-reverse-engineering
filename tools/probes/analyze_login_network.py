import sys
import struct
import pefile
import capstone

def analyze_binary(dll_path):
    print(f"=== Analyzing {dll_path} ===")
    pe = pefile.PE(dll_path)
    base = pe.OPTIONAL_HEADER.ImageBase
    print(f"ImageBase: {hex(base)}")

    # Find string LoginDevMode
    raw_data = open(dll_path, 'rb').read()
    str_offset = raw_data.find(b"LoginDevMode")
    if str_offset == -1:
        print("LoginDevMode string not found!")
        return

    # Convert offset to RVA and VA
    for sec in pe.sections:
        if sec.PointerToRawData <= str_offset < sec.PointerToRawData + sec.SizeOfRawData:
            str_rva = sec.VirtualAddress + (str_offset - sec.PointerToRawData)
            str_va = base + str_rva
            print(f"String 'LoginDevMode' found at raw: {hex(str_offset)}, RVA: {hex(str_rva)}, VA: {hex(str_va)}")
            break
    else:
        print("Could not map string offset to section!")
        return

    # Find references to str_va in code sections
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    needle = struct.pack("<I", str_va)

    for sec in pe.sections:
        sec_name = sec.Name.decode('utf-8', errors='ignore').strip('\x00')
        sec_data = sec.get_data()
        pos = 0
        while True:
            idx = sec_data.find(needle, pos)
            if idx == -1:
                break
            ref_rva = sec.VirtualAddress + idx
            ref_va = base + ref_rva
            print(f"\n[+] Reference to LoginDevMode in {sec_name} at VA {hex(ref_va)}:")

            # Disassemble surrounding code
            start_idx = max(0, idx - 40)
            end_idx = min(len(sec_data), idx + 80)
            dis_code = sec_data[start_idx:end_idx]
            dis_start_va = base + sec.VirtualAddress + start_idx

            for ins in md.disasm(dis_code, dis_start_va):
                mark = "==>" if ins.address <= ref_va < ins.address + ins.size else "   "
                print(f"  {mark} {hex(ins.address)}: {ins.mnemonic} {ins.op_str}")

            pos = idx + 1

if __name__ == "__main__":
    analyze_binary(r"targets\district-187\client-rebirth\Game\GameClient.dll")
