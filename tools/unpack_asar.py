#!/usr/bin/env python3
"""
Lightweight Pure-Python ASAR Unpacker for Electron Applications
Supports unpacking standard Electron asar archives without requiring npm or node.
"""

import json
import os
import struct
import sys

def unpack_asar(asar_path: str, output_dir: str):
    asar_path = os.path.abspath(asar_path)
    output_dir = os.path.abspath(output_dir)
    print(f"[*] Unpacking ASAR: {asar_path} -> {output_dir}")

    with open(asar_path, "rb") as f:
        header_raw = f.read(16)
        u1, u2, u3, u4 = struct.unpack("<IIII", header_raw)
        if u1 != 4:
            raise ValueError(f"Invalid ASAR magic: {u1} (expected 4)")

        json_bytes = f.read(u4)
        metadata = json.loads(json_bytes.decode("utf-8"))

        # In ASAR (Chromium Pickle format), the payload data starts at 8 + u2
        data_base = 8 + u2
        print(f"[+] ASAR header size: {u2} bytes, json string: {u4} bytes. Data starts at: {data_base}")

        extracted_count = 0
        total_bytes = 0

        def extract_node(node, current_path):
            nonlocal extracted_count, total_bytes
            if "files" in node:
                os.makedirs(current_path, exist_ok=True)
                for name, child in node["files"].items():
                    extract_node(child, os.path.join(current_path, name))
            elif "size" in node and "offset" in node:
                size = node["size"]
                offset = int(node["offset"])
                os.makedirs(os.path.dirname(current_path), exist_ok=True)
                f.seek(data_base + offset)
                file_data = f.read(size)
                with open(current_path, "wb") as out_f:
                    out_f.write(file_data)
                extracted_count += 1
                total_bytes += size
                if extracted_count % 100 == 0:
                    print(f"    ... extracted {extracted_count} files ({total_bytes / 1024 / 1024:.2f} MB)")

        extract_node(metadata, output_dir)
        print(f"[SUCCESS] Extracted {extracted_count} files ({total_bytes / 1024 / 1024:.2f} MB) to {output_dir}")

if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else r"targets\dd-classico\extracted\app\runtime\resources\app.asar"
    dst = sys.argv[2] if len(sys.argv) > 2 else r"targets\dd-classico\extracted\asar_unpacked"
    unpack_asar(src, dst)
