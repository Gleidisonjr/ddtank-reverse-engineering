import struct
with open(r'targets\district-187\client\S2\Game\Game.Res00', 'rb') as f:
    header = f.read(16)
    magic, ver, num_files, dir_count = struct.unpack('<4sIII', header)
    f.seek(16 + dir_count * 16)
    dir_str_block = f.read(100000)
    f.seek(16)
    for i in range(25):
        s_off, child, sib, cnt = struct.unpack('<IIII', f.read(16))
        end = dir_str_block.find(b'\0', s_off)
        print(f"[{i}] s_off={s_off} -> \"{dir_str_block[s_off:end].decode('latin1')}\" (cnt={cnt})")
