import os
import struct
import zlib

def extract_from_archive(res00_path, resdt_path, dest_root, patterns):
    print(f"[*] Extracting patterns {patterns} from {res00_path}...")
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
                        print(f"[-] Decompress err for {full_rel}: {e}")
                        decomp = comp_data
                else:
                    decomp = comp_data
                    
                target_path = os.path.join(dest_root, full_rel)
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with open(target_path, "wb") as f_out:
                    f_out.write(decomp)
                print(f"[+] Extracted: {full_rel} ({len(decomp)} bytes) -> {target_path}")
                extracted += 1
                
        print(f"[*] Done. Extracted {extracted} files from {res00_path}.")

if __name__ == "__main__":
    base = r"targets\district-187\client-rebirth"
    # Extract from Game.Res00
    extract_from_archive(
        os.path.join(base, r"Game\Game.Res00"),
        os.path.join(base, r"Game\Game.ResDt"),
        base,
        ["database", "gamdb", "strdb"]
    )
    # Extract from Update_1.Res00 if exists
    if os.path.exists(os.path.join(base, r"Game\Update_1.Res00")):
        extract_from_archive(
            os.path.join(base, r"Game\Update_1.Res00"),
            os.path.join(base, r"Game\Update_1.ResDt"),
            base,
            ["database", "gamdb", "strdb"]
        )
