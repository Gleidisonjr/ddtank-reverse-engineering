import hashlib, os, json, urllib.request, ssl

ctx = ssl._create_unverified_context()
req = urllib.request.Request('https://gamefiles.mdcreative.tr/manifest.json', headers={'User-Agent': 'Mozilla/5.0'})
m = json.loads(urllib.request.urlopen(req, context=ctx).read())

local_base = r'targets/district-187/client/S2'

to_download = []
total_bytes_to_dl = 0

for f in m['dosyalar']:
    if f['yol'].startswith('acik-kaynak-launcher/'):
        continue
    rel = f['yol'].replace('/', '\\')
    loc = os.path.join(local_base, rel)
    needs_dl = True
    if os.path.exists(loc):
        if os.path.getsize(loc) == f['boyut']:
            h = hashlib.sha256(open(loc, 'rb').read()).hexdigest()
            if h == f['sha256']:
                needs_dl = False
    if needs_dl:
        to_download.append(f)
        total_bytes_to_dl += f['boyut']

print(f"Files to download: {len(to_download)}")
print(f"Total download size: {total_bytes_to_dl / (1024*1024):.2f} MB")
for f in to_download[:15]:
    print(f"  {f['boyut']/1024:.1f} KB - {f['yol']}")
