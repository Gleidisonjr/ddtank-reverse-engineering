import os
import sys
import json
import ssl
import gzip
import hashlib
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(encoding='utf-8')

HD_MANIFEST_URL = 'https://gamefileshd.mdcreative.tr/manifest.json'
HD_OBJECTS_URL = 'https://gamefileshd.mdcreative.tr/objects/'
CLIENT_DIR = os.path.abspath(r'targets/district-187/client-rebirth')
GAME_DIR = os.path.join(CLIENT_DIR, 'Game')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        return json.loads(resp.read().decode('utf-8'))

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def download_stream(url, dest_path, expected_hash, expected_size):
    tmp_path = dest_path + '.part'
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    h = hashlib.sha256()
    downloaded = 0
    
    with urllib.request.urlopen(req, context=ctx, timeout=60) as resp, open(tmp_path, 'wb') as out_f:
        first_chunk = resp.read(65536)
        is_gzip = (first_chunk[:2] == b'\x1f\x8b')
        
        if is_gzip:
            # If gzipped, read all and decompress
            rest = resp.read()
            decomp = gzip.decompress(first_chunk + rest)
            out_f.write(decomp)
            h.update(decomp)
            downloaded = len(decomp)
        else:
            out_f.write(first_chunk)
            h.update(first_chunk)
            downloaded = len(first_chunk)
            while chunk := resp.read(1048576): # 1MB chunks
                out_f.write(chunk)
                h.update(chunk)
                downloaded += len(chunk)
                
    actual_hash = h.hexdigest().lower()
    if actual_hash != expected_hash.lower():
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise ValueError(f"Hash mismatch for {dest_path}: got {actual_hash}, expected {expected_hash}")
        
    if os.path.exists(dest_path):
        os.remove(dest_path)
    os.rename(tmp_path, dest_path)
    return downloaded

def update_archcfg():
    archcfg_path = os.path.join(CLIENT_DIR, 'Default.archcfg')
    hd_files = []
    for i in range(1, 10):
        res00 = os.path.join(GAME_DIR, f"HD{i}.Res00")
        resdt = os.path.join(GAME_DIR, f"HD{i}.ResDt")
        if os.path.exists(res00) and os.path.exists(resdt):
            hd_files.append(f"game\\\\HD{i}.Res00")
            
    lines = [
        "game\\\\Game.Res00",
        "game\\\\Update_1.Res00",
        "game\\\\Update_2.Res00"
    ] + hd_files
    
    content = "\n".join(lines)
    with open(archcfg_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"[+] Default.archcfg updated with {len(hd_files)} HD archives!")

def main():
    print(f"[*] Fetching HD texture pack manifest from {HD_MANIFEST_URL}...")
    manifest = fetch_json(HD_MANIFEST_URL)
    version = manifest.get('surum', 'unknown')
    dosyalar = manifest.get('dosyalar', [])
    print(f"[*] HD Version: {version}, total archives: {len(dosyalar)}")
    
    to_download = []
    total_bytes = 0
    for f in dosyalar:
        rel = f['yol'].replace('/', os.sep)
        dest = os.path.join(CLIENT_DIR, rel)
        exp_hash = f['sha256']
        exp_size = f['boyut']
        
        if os.path.exists(dest) and os.path.getsize(dest) == exp_size:
            if sha256_file(dest) == exp_hash:
                print(f"  [=] Already present: {f['yol']} ({exp_size / (1024*1024):.1f} MB)")
                continue
                
        to_download.append((f['yol'], dest, exp_hash, exp_size))
        total_bytes += exp_size
        
    print(f"[*] Archives to download: {len(to_download)} ({total_bytes / (1024*1024):.2f} MB)")
    if not to_download:
        print("[+] All HD textures are already downloaded and verified!")
        update_archcfg()
        return
        
    def worker(item):
        yol, dest, exp_hash, exp_size = item
        url = f"{HD_OBJECTS_URL}{exp_hash}"
        print(f"  [>] Starting download: {yol} ({exp_size / (1024*1024):.1f} MB)...")
        downloaded = download_stream(url, dest, exp_hash, exp_size)
        print(f"  [+] Finished: {yol} ({downloaded / (1024*1024):.1f} MB)")
        return yol
        
    # Download with 4 threads for optimal throughput
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(worker, item): item for item in to_download}
        for fut in as_completed(futures):
            fut.result()
            
    print("\n[+] All HD archives successfully downloaded and verified!")
    update_archcfg()

if __name__ == '__main__':
    main()
