import urllib.request, ssl, sys
sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request('https://s2rebirth.com/js/uygulama.js', headers={'User-Agent': 'Mozilla/5.0'})
js = urllib.request.urlopen(req, context=ctx, timeout=10).read().decode('utf-8', errors='ignore')
idx = js.find('/kayit')
while idx != -1:
    print("--- MATCH AT", idx)
    print(js[max(0, idx-200):idx+400])
    idx = js.find('/kayit', idx+1)
