import os, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
root = r"C:\Users\dopamine\Desktop\Projetos\Reverse Engineering\targets\district-187\client-rebirth"
now = time.time()
rows = []
for dp, dn, fn in os.walk(root):
    for f in fn:
        p = os.path.join(dp, f)
        try:
            m = os.path.getmtime(p)
        except OSError:
            continue
        if now - m < 1800:
            rows.append((m, p, os.path.getsize(p)))
for m, p, s in sorted(rows)[-25:]:
    print(time.strftime('%H:%M:%S', time.localtime(m)), s, os.path.relpath(p, root))
