import os
import sys
import json
import ssl
import gzip
import hashlib
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(encoding='utf-8')

CLIENT_DIR = os.path.abspath(r'targets/district-187/client-rebirth')
LOCAL_S2_DIR = os.path.abspath(r'targets/district-187/client/S2')
MANIFEST_URL = 'https://gamefiles.mdcreative.tr/manifest.json'
OBJECTS_URL = 'https://gamefiles.mdcreative.tr/objects/'
EN_MANIFEST_URL = 'https://gamefiles.mdcreative.tr/en/manifest.json'
EN_OBJECTS_URL = 'https://gamefiles.mdcreative.tr/en/objects/'

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

def download_object(base_url, sha256_hash, dest_path, expected_hash):
    tmp_path = dest_path + '.downloading'
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    
    url = f"{base_url}{sha256_hash}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        raw = resp.read()
    
    if raw[:2] == b'\x1f\x8b':
        decomp = gzip.decompress(raw)
    else:
        decomp = raw
        
    actual_hash = hashlib.sha256(decomp).hexdigest()
    if actual_hash.lower() != expected_hash.lower():
        raise ValueError(f"Hash mismatch for {dest_path}: got {actual_hash}, expected {expected_hash}")
        
    with open(tmp_path, 'wb') as f:
        f.write(decomp)
    if os.path.exists(dest_path):
        os.remove(dest_path)
    os.rename(tmp_path, dest_path)
    return len(decomp)

def main():
    print(f"[*] Setting up clean S2 Rebirth client in: {CLIENT_DIR}")
    os.makedirs(CLIENT_DIR, exist_ok=True)
    
    print("[*] Fetching official manifest...")
    manifest = fetch_json(MANIFEST_URL)
    version = manifest.get('surum', 'unknown')
    dosyalar = manifest.get('dosyalar', [])
    print(f"[*] Manifest version: {version}, total files: {len(dosyalar)}")
    
    # 1. Process base files: reuse local matches or queue for download
    to_download = []
    reused = 0
    
    for item in dosyalar:
        rel_path = item['yol'].replace('/', os.sep)
        # Skip open-source launcher dev sources inside client game dir
        if item['yol'].startswith('acik-kaynak-launcher/'):
            continue
            
        dest = os.path.join(CLIENT_DIR, rel_path)
        expected_hash = item['sha256']
        expected_size = item.get('boyut', 0)
        
        # Check if already present and verified in CLIENT_DIR
        if os.path.exists(dest) and os.path.getsize(dest) == expected_size:
            if sha256_file(dest) == expected_hash:
                continue
                
        # Check if existing file in LOCAL_S2_DIR matches
        local_src = os.path.join(LOCAL_S2_DIR, rel_path)
        if os.path.exists(local_src) and os.path.getsize(local_src) == expected_size:
            if sha256_file(local_src) == expected_hash:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                if os.path.exists(dest):
                    os.remove(dest)
                try:
                    os.link(local_src, dest)
                except Exception:
                    import shutil
                    shutil.copy2(local_src, dest)
                reused += 1
                continue
                
        to_download.append((OBJECTS_URL, item['sha256'], dest, expected_hash, item['yol'], expected_size))
        
    print(f"[*] Reused from local archive: {reused} files")
    print(f"[*] Files to download from CDN: {len(to_download)}")
    
    total_dl_bytes = sum(x[5] for x in to_download)
    print(f"[*] Total download volume: {total_dl_bytes / (1024*1024):.2f} MB")
    
    def worker(task):
        base_url, sha, dest, exp_hash, rel, sz = task
        try:
            download_object(base_url, sha, dest, exp_hash)
            return True, rel, sz, None
        except Exception as e:
            return False, rel, sz, str(e)
            
    completed = 0
    failed = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(worker, t): t for t in to_download}
        for fut in as_completed(futures):
            ok, rel, sz, err = fut.result()
            completed += 1
            if ok:
                if completed % 25 == 0 or completed == len(to_download):
                    print(f"  [{completed}/{len(to_download)}] Downloaded {rel} ({sz/1024:.1f} KB)")
            else:
                print(f"  [!] FAILED: {rel} - {err}")
                failed.append(rel)
                
    if failed:
        print(f"[!] Warning: {len(failed)} files failed to download: {failed}")
    else:
        print("[+] All base game files successfully assembled!")
        
    # 2. English Interface & Audio Pack
    print("\n[*] Fetching English language pack manifest...")
    try:
        en_manifest = fetch_json(EN_MANIFEST_URL)
        en_dosyalar = en_manifest.get('dosyalar', [])
        print(f"[*] English pack files: {len(en_dosyalar)}")
        
        en_to_dl = []
        for item in en_dosyalar:
            rel_path = item['yol'].replace('/', os.sep)
            dest = os.path.join(CLIENT_DIR, rel_path)
            expected_hash = item['sha256']
            expected_size = item.get('boyut', 0)
            
            if os.path.exists(dest) and os.path.getsize(dest) == expected_size:
                if sha256_file(dest) == expected_hash:
                    continue
            en_to_dl.append((EN_OBJECTS_URL, item['sha256'], dest, expected_hash, item['yol'], expected_size))
            
        print(f"[*] English files to download: {len(en_to_dl)}")
        en_completed = 0
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = {pool.submit(worker, t): t for t in en_to_dl}
            for fut in as_completed(futures):
                ok, rel, sz, err = fut.result()
                en_completed += 1
                if ok:
                    if en_completed % 25 == 0 or en_completed == len(en_to_dl):
                        print(f"  [{en_completed}/{len(en_to_dl)}] Installed EN {rel} ({sz/1024:.1f} KB)")
                else:
                    print(f"  [!] FAILED EN: {rel} - {err}")
                    
        print("[+] English language pack applied successfully!")
    except Exception as e:
        print(f"[!] Error fetching English pack: {e}")
        
    print("\n[+] S2 Rebirth Client preparation complete!")

if __name__ == '__main__':
    main()
