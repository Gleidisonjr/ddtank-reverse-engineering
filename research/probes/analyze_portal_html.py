import re
import os

with open(r'targets\dd-classico\extracted\dumped\live_ddclassico_portal.html', 'r', encoding='utf-8', errors='ignore') as f:
    html = f.read()

forms = re.findall(r'<form[^>]*action=["\']([^"\']+)["\']', html)
print('Forms actions:', forms)

links = re.findall(r'href=["\']([^"\']+)["\']', html)
interesting_links = [l for l in set(links) if any(k in l.lower() for k in ['game', 'server', 'play', 'login', 'entrar', 'jogar', 'api', 'swf', 'flash', 'account'])]
print('Interesting links:', interesting_links)

scripts = re.findall(r'src=["\']([^"\']+)["\']', html)
print('Scripts count:', len(scripts))
for s in scripts:
    print('  Script:', s)

# Search for any inline json or servers data
server_matches = re.findall(r'server[s]?\s*[:=]\s*(\[[^\]]+\])', html, re.IGNORECASE)
print('Server matches in JS:', server_matches)
