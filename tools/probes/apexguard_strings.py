import os, re, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
root = r"C:\Users\dopamine\Desktop\Projetos\Reverse Engineering\targets\district-187\client-rebirth"
for f in ["D3DX9_43.dll", "D3DX9_43.dll.proxy_bak", "ApexGuard.dll", "TheRaw.exe"]:
    p = os.path.join(root, f)
    print(f, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(p))))
data = open(os.path.join(root, "ApexGuard.dll"), 'rb').read()
print("\n-- ApexGuard.dll ASCII/UTF16 strings of interest --")
pat = re.compile(rb'[\x20-\x7e]{5,}')
for m in pat.finditer(data):
    s = m.group().decode()
    if re.search(r'd3d|dx|S2-3|hash|sha|crc|verify|system32|syswow|\.dll|\.exe', s, re.I):
        print(s[:140])
u = re.compile(rb'(?:[\x20-\x7e]\x00){5,}')
for m in u.finditer(data):
    s = m.group().decode('utf-16le')
    if re.search(r'd3d|dx|S2-3|hash|verify|\.dll', s, re.I):
        print("U16:", s[:140])
