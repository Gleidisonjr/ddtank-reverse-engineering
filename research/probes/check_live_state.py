import re, subprocess, sys, psutil
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LOG = r"C:\Users\dopamine\.gemini\antigravity-cli\brain\e317532f-f08a-492b-8467-49f769504e7f\.system_generated\tasks\task-4269.log"
print("TheRaw:", [(p.pid, p.status()) for p in psutil.process_iter(['name']) if p.info['name'] == 'TheRaw.exe'])
for c in psutil.net_connections('tcp'):
    if c.raddr and c.raddr.port == 12000:
        print("conn:", c.laddr.port, c.status, c.pid)
lines = open(LOG, encoding='utf-8', errors='replace').read().splitlines()
keys = re.compile(r"Client connected|closed connection|Handshake|Keepalive|Apex|JoyGameLogin|Unknown|error", re.I)
for l in [x for x in lines if keys.search(x)][-20:]:
    print(l)
