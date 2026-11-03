import urllib.request, ssl, re, sys
sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request('https://s2rebirth.com/js/hesap.js', headers={'User-Agent': 'Mozilla/5.0'})
text = urllib.request.urlopen(req, context=ctx).read().decode('utf-8', errors='ignore')

print("=== Endpoints em hesap.js ===")
for m in re.finditer(r"istek\(\s*['\"]([^'\"]+)['\"](?:\s*,\s*\{[^}]*method:\s*['\"]([^'\"]+)['\"])?", text):
    endpoint = m.group(1)
    method = m.group(2) or 'GET'
    print(f"  {method:6} /api/oyuncu{endpoint}")

req2 = urllib.request.Request('https://s2rebirth.com/js/ekran-siralama.js', headers={'User-Agent': 'Mozilla/5.0'})
text2 = urllib.request.urlopen(req2, context=ctx).read().decode('utf-8', errors='ignore')

print("\n=== Endpoints em ekran-siralama.js ===")
for m in re.finditer(r"['\"](/api/[^'\"]+)['\"]", text2):
    print(f"  GET    {m.group(1)}")
