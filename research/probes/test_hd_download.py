import urllib.request, json, ssl, gzip

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request('https://gamefileshd.mdcreative.tr/manifest.json', headers={'User-Agent': 'Mozilla/5.0'})
m = json.loads(urllib.request.urlopen(req, context=ctx).read())
hd1 = [f for f in m['dosyalar'] if f['yol'] == 'Game/HD1.Res00'][0]
print('HD1 info:', hd1)
url = f'https://gamefileshd.mdcreative.tr/objects/{hd1["sha256"]}'
raw = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), context=ctx).read()
if raw[:2] == b'\x1f\x8b':
    raw = gzip.decompress(raw)
print('Downloaded HD1.Res00 successfully, size:', len(raw))
