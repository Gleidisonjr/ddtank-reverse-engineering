import urllib.request, ssl, re, sys
sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

for f in ['js/hesap.js', 'js/ekran-portal.js', 'js/veri.js', 'js/ekran-siralama.js']:
    url = f'https://s2rebirth.com/{f}'
    try:
        content = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), context=ctx).read().decode('utf-8', errors='ignore')
        print(f"=== {f} ({len(content)} bytes) ===")
        # Find API endpoints
        apis = re.findall(r'["\'](/api/[^"\']+)["\']', content)
        if apis:
            print("  API routes:", list(set(apis)))
        # Find comments or function names
        funcs = re.findall(r'(?:async\s+)?function\s+([a-zA-Z0-9_]+)|export\s+(?:async\s+)?function\s+([a-zA-Z0-9_]+)', content)
        fn_names = [a or b for a, b in funcs if a or b]
        print("  Functions:", fn_names[:12])
    except Exception as e:
        print(f"Error {f}: {e}")
