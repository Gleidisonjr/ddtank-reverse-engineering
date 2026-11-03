import pefile, capstone

pe = pefile.PE(r'targets\district-187\client-rebirth\Game\GameClient.dll')
cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
rva = 0x10005630 - 0x10000000
data = pe.get_data(rva, 0x10005e35 - 0x10005630)

dll_strings = ['ChangeNickName', 'ChangeClanName']
for ins in cs.disasm(data, 0x10005630):
    if ins.mnemonic in ('push', 'mov') and ins.op_str.startswith('0x10482'):
        va = int(ins.op_str.split()[-1], 16)
        rva_s = va - 0x10000000
        try:
            s = pe.get_string_at_rva(rva_s).decode('latin1')
            if s and s not in dll_strings and s not in ('error', 'vector<T> too long'):
                dll_strings.append(s)
        except:
            pass

with open(r'targets\district-187\client-rebirth\Database\Table\FunctionList.csv', 'r', encoding='latin1') as f:
    lines = [l.strip('\r\n') for l in f.readlines() if l.strip('\r\n')]

print(f'CSV lines (non-empty): {len(lines)}')
header = lines[0]
data_rows = lines[1:]

mismatches = 0
for i, row in enumerate(data_rows):
    cols = row.split(',')
    idx_val = cols[0]
    name_val = cols[1]
    if name_val in dll_strings:
        dll_idx = dll_strings.index(name_val)
        print(f'Row {i+1:2d}: {idx_val} -> "{name_val}" MATCHES DLL item [{dll_idx}]')
    else:
        print(f'Row {i+1:2d}: {idx_val} -> "{name_val}" MISMATCH/NOT FOUND in DLL!')
        mismatches += 1

print(f'\nTotal non-empty data rows: {len(data_rows)}, Mismatches: {mismatches}')
