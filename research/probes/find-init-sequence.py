with open(r'targets\district-187\client\S2\Game\GameClient.dll', 'rb') as f:
    data = f.read()

import re
matches = [m.start() for m in re.finditer(rb'm_pSteamWebBrowserMgr', data)]
for m in matches:
    print(f"Found 'm_pSteamWebBrowserMgr' at file offset 0x{m:06X}")
    # find surrounding strings
    chunk = data[m-100:m+200]
    for s in re.findall(rb'[\x20-\x7E]{4,}', chunk):
        print("  ", s.decode('latin1'))
