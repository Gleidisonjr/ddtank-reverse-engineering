import urllib.request
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

urls = [
    "https://resource.ddclassico.com/flash/config.xml",
    "https://resource.ddclassico.com/request/TemplateAllList.xml",
    "https://resource.ddclassico.com/request/LoadItemsCategory.xml",
    "https://resource.ddclassico.com/request/BallList.xml",
    "https://resource.ddclassico.com/request/BombConfig.xml",
    "https://game.ddclassico.com/request/TemplateAllList.xml",
    "https://game.ddclassico.com/request/LoadItemsCategory.xml",
    "https://game.ddclassico.com/request/BallList.xml"
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) DDClassico/2.0.5 Chrome/87.0.4280.141 Electron/11.5.0 Safari/537.36",
    "X-HWID": "30043ec11b51829ee9dd2a04439c29929285038cbe22f256ea0036666874bb7c"
}

for u in urls:
    req = urllib.request.Request(u, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
            content = resp.read()
            print(f"[OK 200] {u} ({len(content)} bytes, type: {resp.headers.get('Content-Type')})")
            if content.startswith(b'<?xml') or b'<Result' in content or b'<ItemTemplate' in content or b'<config' in content:
                print(f"  Valid XML! Snippet: {content[:150]}")
    except Exception as e:
        print(f"[FAIL] {u}: {e}")
