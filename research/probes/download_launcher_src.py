import urllib.request, json, ssl, gzip, os

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request('https://gamefiles.mdcreative.tr/manifest.json', headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
    manifest = json.loads(r.read().decode('utf-8'))

files = manifest.get('dosyalar', [])
out_dir = r'targets/district-187/s2rebirth-launcher-src'
os.makedirs(out_dir, exist_ok=True)

launcher_files = [f for f in files if f.get('yol', '').startswith('acik-kaynak-launcher/')]
print(f"Found {len(launcher_files)} launcher source files. Downloading...")

for f in launcher_files:
    yol = f.get('yol')
    sha = f.get('sha256')
    rel = yol.replace('acik-kaynak-launcher/', '')
    dest = os.path.join(out_dir, rel)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    
    url = f'https://gamefiles.mdcreative.tr/objects/{sha}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            raw = r.read()
            # check if gzip
            if raw[:2] == b'\x1f\x8b':
                decomp = gzip.decompress(raw)
            else:
                decomp = raw
            with open(dest, 'wb') as out_f:
                out_f.write(decomp)
            print(f"Downloaded {rel} ({len(decomp)} bytes)")
    except Exception as e:
        print(f"Failed {rel}: {e}")
