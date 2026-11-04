import urllib.request, ssl, sys, json
sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

for name in ['rutbeler.json', 'magaza.json', 'haritalar.json', 'unvanlar.json', 'esyalar.json']:
    u = f'https://s2rebirth.com/veri/{name}'
    try:
        raw = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), context=ctx).read()
        data = json.loads(raw)
        print(f"=== {name} ({len(raw)/1024:.1f} KB) ===")
        if name == 'rutbeler.json':
            ranks = data.get('rutbeler', [])
            print(f"  Total Patentes/Ranks: {len(ranks)}")
            for r in ranks[:6]:
                print(f"    Lv {r.get('seviye')}: {r.get('ad')} (XP: {r.get('altSinir')} - {r.get('ustSinir')})")
        elif name == 'magaza.json':
            cats = data.get('kategoriler', [])
            print(f"  Categorias da Loja: {len(cats)}")
            for c in cats:
                print(f"    - {c.get('ad')} ({len(c.get('gruplar', []))} itens)")
        elif name == 'haritalar.json':
            maps = data.get('haritalar', [])
            print(f"  Total Mapas: {len(maps)}")
            for m in maps[:6]:
                print(f"    - {m.get('ad')} ({m.get('mod')})")
        elif name == 'esyalar.json':
            items = data.get('esyalar', [])
            print(f"  Total Armas/Itens no Catálogo: {len(items)}")
    except Exception as e:
        print(f"Error {name}: {e}")
