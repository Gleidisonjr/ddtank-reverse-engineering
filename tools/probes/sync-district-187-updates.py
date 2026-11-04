#!/usr/bin/env python3
"""
Sync missing update files and game tables from GitHub repository (cdgame-w/conf)
into the District 187 client directory.
"""
import hashlib
import json
import os
import urllib.request

CLIENT_DIR = r"targets\district-187\client\S2"
FILES_JSON_URL = "https://raw.githubusercontent.com/cdgame-w/conf/main/files.json"
BASE_URL = "https://raw.githubusercontent.com/cdgame-w/conf/main/files/"

def get_file_hash(filepath):
    if not os.path.exists(filepath):
        return None
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def sync_updates():
    print(f"[*] Fetching manifest from {FILES_JSON_URL}...")
    req = urllib.request.Request(FILES_JSON_URL, headers={"User-Agent": "District187Sync/1.0"})
    with urllib.request.urlopen(req) as response:
        manifest = json.loads(response.read().decode())

    print(f"[*] Manifest contains {len(manifest)} files.")
    
    for item in manifest:
        rel_path = item["file"].replace("/", os.sep)
        expected_hash = item["hash"].upper()
        local_path = os.path.join(CLIENT_DIR, rel_path)
        
        current_hash = get_file_hash(local_path)
        if current_hash == expected_hash:
            print(f"[OK] {rel_path} (Hash matched)")
            continue
            
        print(f"[FETCH] Downloading {rel_path}...")
        url = BASE_URL + item["file"]
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        dl_req = urllib.request.Request(url, headers={"User-Agent": "District187Sync/1.0"})
        with urllib.request.urlopen(dl_req) as dl_resp, open(local_path, "wb") as f_out:
            while chunk := dl_resp.read(65536):
                f_out.write(chunk)
                
        new_hash = get_file_hash(local_path)
        if new_hash == expected_hash:
            print(f"[VERIFIED] {rel_path} downloaded and verified successfully.")
        else:
            print(f"[WARN] {rel_path} hash mismatch: got {new_hash}, expected {expected_hash}")

if __name__ == "__main__":
    sync_updates()
