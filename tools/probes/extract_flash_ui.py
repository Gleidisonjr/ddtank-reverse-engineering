import os
import struct
import zlib
import time

def extract_archive_pattern(res00_path, dest_roots, patterns):
    resdt_path = res00_path.replace(".Res00", ".ResDt")
    if not os.path.exists(res00_path) or not os.path.exists(resdt_path):
        print(f"[-] Missing archive: {res00_path}")
        return

    print(f"[*] Extracting from {res00_path}...")
    with open(res00_path, "rb") as f_idx, open(resdt_path, "rb") as f_data:
        header = f_idx.read(32)
        magic, version, str_table_size, num_dirs, num_files, extra1, extra2, extra3 = struct.unpack("<8I", header)
        
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
            str_off, child_idx, next_idx, file_cnt = struct.unpack("<IIII", d_entry)
            actual_dir_off = str_off + 16
            end = str_table.find(b"\x00", actual_dir_off)
            dir_name = str_table[actual_dir_off:end].decode("ascii", errors="ignore") if end != -1 else ""
            dir_file_mapping.append((dir_name, file_cnt))
            
        file_to_dir = {}
        curr = 0
        for d_name, cnt in dir_file_mapping:
            for _ in range(cnt):
                file_to_dir[curr] = d_name
                curr += 1
                
        f_idx.seek(32 + actual_str_size)
        extracted = 0
        for i in range(num_files):
            entry = f_idx.read(48)
            str_offset, res_offset, comp_size, uncomp_size, flags = struct.unpack("<IQQQI", entry[:32])
            actual_str_offset = str_offset + 16
            end = str_table.find(b"\x00", actual_str_offset)
            fname = str_table[actual_str_offset:end].decode("ascii", errors="ignore") if end != -1 else ""
            dir_name = file_to_dir.get(i, "")
            full_rel = os.path.join(dir_name, fname)
            
            match = False
            for p in patterns:
                if p.lower() in full_rel.lower():
                    match = True
                    break
                    
            if match:
                f_data.seek(res_offset)
                comp_data = f_data.read(comp_size)
                if flags == 9 or comp_data.startswith(b"\x78\xda") or comp_data.startswith(b"\x78\x9c") or comp_data.startswith(b"\x78\x01"):
                    try:
                        decomp = zlib.decompress(comp_data)
                    except Exception as e:
                        decomp = comp_data
                else:
                    decomp = comp_data
                    
                for dest_root in dest_roots:
                    target_file = os.path.join(dest_root, full_rel)
                    target_dir = os.path.dirname(target_file)
                    os.makedirs(target_dir, exist_ok=True)
                    with open(target_file, "wb") as out_f:
                        out_f.write(decomp)
                extracted += 1
                
        print(f"[+] Extracted {extracted} files from {res00_path}")

def main():
    root = os.path.abspath(r"targets\district-187\client-rebirth")
    game_sub = os.path.join(root, "Game")
    roots = [root, game_sub]
    
    # Kill any lingering TheRaw.exe
    import subprocess
    subprocess.run(["taskkill", "/f", "/im", "TheRaw.exe"], capture_output=True)
    time.sleep(1)
    
    archives = [
        os.path.join(game_sub, "Game.Res00"),
        os.path.join(game_sub, "Update_1.Res00"),
        os.path.join(game_sub, "Update_2.Res00")
    ]
    
    for arc in archives:
        extract_archive_pattern(arc, roots, ["Interface\\Flash", "Interface/Flash", "Logo."])

if __name__ == "__main__":
    main()
