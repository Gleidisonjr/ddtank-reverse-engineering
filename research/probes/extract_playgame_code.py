import re
import json

with open(r'targets\dd-classico\extracted\dumped\playgame.html', 'r', encoding='utf-8') as f:
    html = f.read()

scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
for s in scripts:
    if '"code":' in s:
        idx = s.find('"code":')
        print(s[idx:idx+1500])
