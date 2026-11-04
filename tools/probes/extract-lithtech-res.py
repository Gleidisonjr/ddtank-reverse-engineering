#!/usr/bin/env python3
"""
LithTech Jupiter EX 'HBEK' Resource Archive Unpacker (.Res00 / .ResDt)
Specifically reversed for District 187: Sin Streets / S2 Online.
Preserves full authentic directory tree recovered from the internal Directory Table.

Author: Gleidison Carvalho & Antigravity (2026-11-02)
"""
import argparse
import os
import struct
import sys
import zlib

def unpack_hbek(res00_path, resdt_path, output_dir, filter_ext=None, pattern=None, max_extract=None, flat=False):
    if not os.path.exists(res00_path):
        print(f"[-] Index file not found: {res00_path}")
        return
    if not os.path.exists(resdt_path):
        print(f"[-] Data file not found: {resdt_path}")
        return

    os.makedirs(output_dir, exist_ok=True)

    with open(res00_path, "rb") as f_idx, open(resdt_path, "rb") as f_data:
        header = f_idx.read(32)
        magic, version, str_table_size, num_dirs, num_files, extra1, extra2, extra3 = struct.unpack("<8I", header)
        
        if magic != 0x4B454248: # 'HBEK'
            print(f"[-] Invalid magic: 0x{magic:08X} (expected HBEK)")
            return

        print(f"[+] HBEK Archive v{version}: {num_dirs} directories, {num_files} files.")
        
        # Calculate actual string table size based on file structure
        f_idx.seek(0, 2)
        total_idx_size = f_idx.tell()
        expected_tables_size = (num_files * 48) + (num_dirs * 16)
        actual_str_size = total_idx_size - 32 - expected_tables_size
        
        # Read string table
        f_idx.seek(32)
        str_table = f_idx.read(actual_str_size)
        
        # Read directory table to map sequential files to directories
        f_idx.seek(32 + actual_str_size + (num_files * 48))
        dir_file_mapping = []
        for d_idx in range(num_dirs):
            d_entry = f_idx.read(16)
            str_off, child_idx, next_idx, file_cnt = struct.unpack("<IIII", d_entry)
            actual_dir_off = str_off + 16
            end = str_table.find(b"\x00", actual_dir_off)
            dir_name = str_table[actual_dir_off:end].decode("ascii", errors="ignore") if end != -1 else ""
            dir_file_mapping.append((dir_name, file_cnt))
        
        # Build mapping from file index to directory path
        file_to_dir = {}
        curr_file_idx = 0
        for dir_name, count in dir_file_mapping:
            for _ in range(count):
                file_to_dir[curr_file_idx] = dir_name
                curr_file_idx += 1
                
        # Now seek to file table and extract
        f_idx.seek(32 + actual_str_size)
        
        extracted_count = 0
        skipped_count = 0

        for i in range(num_files):
            entry = f_idx.read(48)
            str_offset, res_offset, comp_size, uncomp_size, flags = struct.unpack("<IQQQI", entry[:32])
            
            # str_offset is relative to the string table payload (after the 16-byte root GUID)
            actual_str_offset = str_offset + 16
            end = str_table.find(b"\x00", actual_str_offset)
            fname = str_table[actual_str_offset:end].decode("ascii", errors="ignore") if end != -1 else f"file_{i:06d}.bin"
            
            dir_path = file_to_dir.get(i, "")
            full_rel_path = os.path.join(dir_path, fname) if (not flat and dir_path) else fname
            
            # Filter by extension
            ext = os.path.splitext(fname)[1].lower()
            if filter_ext and ext != filter_ext.lower():
                skipped_count += 1
                continue
                
            # Filter by pattern/keyword in path
            if pattern and pattern.lower() not in full_rel_path.lower():
                skipped_count += 1
                continue
                
            out_file_path = os.path.join(output_dir, full_rel_path.replace("\\", os.sep))
            os.makedirs(os.path.dirname(out_file_path), exist_ok=True)
            
            # Read and decompress
            f_data.seek(res_offset)
            comp_data = f_data.read(comp_size)
            
            if flags == 9 or (comp_data.startswith(b"\x78\xda") or comp_data.startswith(b"\x78\x9c") or comp_data.startswith(b"\x78\x01")):
                try:
                    decomp_data = zlib.decompress(comp_data)
                except Exception:
                    decomp_data = comp_data
            else:
                decomp_data = comp_data
                
            with open(out_file_path, "wb") as f_out:
                f_out.write(decomp_data)
                
            extracted_count += 1
            if extracted_count % 100 == 0 or extracted_count == 1:
                print(f"[EXTRACT] [{extracted_count}] {full_rel_path} ({len(decomp_data)} bytes)")
                
            if max_extract and extracted_count >= max_extract:
                print(f"[*] Reached max extract limit ({max_extract}).")
                break

        print(f"[+] Extraction complete. Extracted: {extracted_count}, Skipped: {skipped_count}.")

def main():
    parser = argparse.ArgumentParser(description="Unpack LithTech Jupiter EX HBEK archives with full directory tree")
    parser.add_argument("--res00", required=True, help="Path to .Res00 index file")
    parser.add_argument("--resdt", required=True, help="Path to .ResDt data file")
    parser.add_argument("--out", required=True, help="Output destination folder")
    parser.add_argument("--ext", help="Filter by file extension (e.g. .model00p, .csv, .dds, .mat00)")
    parser.add_argument("--pattern", help="Filter by path keyword / pattern (e.g. weapons, characters, maps)")
    parser.add_argument("--limit", type=int, help="Limit number of extracted files")
    parser.add_argument("--flat", action="store_true", help="Extract all files flat without directory hierarchy")
    args = parser.parse_args()

    unpack_hbek(args.res00, args.resdt, args.out, filter_ext=args.ext, pattern=args.pattern, max_extract=args.limit, flat=args.flat)

if __name__ == "__main__":
    main()
