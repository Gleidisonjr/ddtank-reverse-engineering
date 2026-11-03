import re

with open(r'targets\dd-classico\extracted\dumped\playgame.html', 'r', encoding='utf-8') as f:
    html = f.read()

embeds = re.findall(r'<embed[^>]+>', html, re.IGNORECASE)
print('Embed tags:', embeds)

objects = re.findall(r'<object[^>]+>', html, re.IGNORECASE)
print('Object tags:', objects)

params = re.findall(r'<param[^>]+>', html, re.IGNORECASE)
print('Param tags count:', len(params))
for p in params:
    print('  Param:', p)

swfs = set(re.findall(r'[\w\-/\.]+\.swf[^\s"\'<>]*', html, re.IGNORECASE))
print('SWF URLs found in playgame.html:', swfs)

scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE)
print('Inline scripts count:', len(scripts))
for i, s in enumerate(scripts):
    if any(k in s.lower() for k in ['flash', 'swf', 'server', 'play', 'token', 'user', 'ddtank']):
        print(f'=== Script {i} ===')
        print(s.strip()[:600])
        print('---')

import json
for s in scripts:
    if '"routes":' in s:
        try:
            data = json.loads(s.strip())
            print('Total routes:', len(data.get('routes', [])))
            for r in data.get('routes', []):
                if any(k in r.lower() for k in ['play', 'game', 'server', 'classic']):
                    print('  Route:', r)
        except Exception as e:
            print('Error parsing route json:', e)
