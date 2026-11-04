import urllib.request
import re
import ssl
import sys

sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = 'https://s2rebirth.com/indir'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

# Search for any http/https link or file
links = re.findall(r'https?://[a-zA-Z0-9_./\-~%?&=+#]+', html)
interesting = set()
for l in links:
    if any(ext in l.lower() for ext in ['.exe', '.zip', '.rar', '.7z', 'drive.google', 'mega.nz', 'mediafire', 'discord', 'cdn']):
        interesting.add(l)

print(f"Total links found: {len(links)}")
print("Interesting links:")
for l in sorted(interesting):
    print(" ", l)

# Let's also check for text around 'indir' or 'Download'
matches = re.findall(r'(.{0,100}(?:indir|download|istemci|client|setup).{0,100})', html, re.I)
print(f"\nText matches ({len(matches)}):")
for m in matches[:10]:
    print("  ->", m.strip())
