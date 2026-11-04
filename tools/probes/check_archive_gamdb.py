import struct

with open(r'targets\district-187\client-rebirth\Game\Game.Res00', 'rb') as f_idx:
    header = f_idx.read(32)
    magic, version, str_table_size, num_dirs, num_files, extra1, extra2, extra3 = struct.unpack('<8I', header)
    f_idx.seek(0, 2)
    total_idx_size = f_idx.tell()
    expected_tables_size = (num_files * 48) + (num_dirs * 16)
    actual_str_size = total_idx_size - 32 - expected_tables_size
    f_idx.seek(32)
    str_table = f_idx.read(actual_str_size)
    f_idx.seek(32 + actual_str_size + (num_files * 48))
    
    dir_file_mapping = []
    for d_idx in range(num_dirs):
        d_entry = f_idx.read(16)
        str_off, child_idx, next_idx, file_cnt = struct.unpack('<IIII', d_entry)
        actual_dir_off = str_off + 16
        end = str_table.find(b'\x00', actual_dir_off)
        dir_name = str_table[actual_dir_off:end].decode('ascii', errors='ignore') if end != -1 else ''
        dir_file_mapping.append((dir_name, file_cnt))
        
    file_to_dir = {}
    curr = 0
    for d_name, cnt in dir_file_mapping:
        for _ in range(cnt):
            file_to_dir[curr] = d_name
            curr += 1
            
    f_idx.seek(32 + actual_str_size)
    for i in range(num_files):
        entry = f_idx.read(48)
        str_offset, res_offset, comp_size, uncomp_size, flags = struct.unpack('<IQQQI', entry[:32])
        actual_str_offset = str_offset + 16
        end = str_table.find(b'\x00', actual_str_offset)
        fname = str_table[actual_str_offset:end].decode('ascii', errors='ignore') if end != -1 else ''
        if 'gamdb' in fname.lower():
            d_name = file_to_dir.get(i, '')
            print(f'File [{i}]: dir="{d_name}", name="{fname}", full="{d_name}\\{fname}", offset=0x{res_offset:x}, comp_size={comp_size}, uncomp_size={uncomp_size}')
