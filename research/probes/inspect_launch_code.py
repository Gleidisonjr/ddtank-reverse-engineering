import urllib.request, json, ssl, gzip, sys
sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request('https://gamefiles.mdcreative.tr/manifest.json', headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
    manifest = json.loads(r.read().decode('utf-8'))

for item in manifest.get('dosyalar', []):
    yol = item.get('yol')
    if yol == 'launcher.cfg':
        sha = item.get('sha256')
        url = f'https://gamefiles.mdcreative.tr/objects/{sha}'
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), context=ctx) as f:
            raw = f.read()
            if raw[:2] == b'\x1f\x8b':
                raw = gzip.decompress(raw)
            print(raw.decode('utf-8', errors='ignore'))
