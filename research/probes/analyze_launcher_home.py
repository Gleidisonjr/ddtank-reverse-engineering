import re

with open(r'targets\dd-classico\extracted\dumped\launcher_home.html', 'r', encoding='utf-8') as f:
    html = f.read()

print('Title:', re.findall(r'<title>(.*?)</title>', html))

forms = re.findall(r'<form[^>]*action=["\']([^"\']+)["\']', html)
print('Forms:', forms)

links = re.findall(r'href=["\']([^"\']+)["\']', html)
print('Links:', [l for l in set(links) if 'classic' in l or 'login' in l or 'account' in l])

# Check for any server items or character select
servers = re.findall(r'class="[^"]*server[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL | re.IGNORECASE)
print('Server divs count:', len(servers))
for s in servers[:5]:
    print('  Server:', s.strip()[:100])
