import glob, os, sys
sys.stdout.reconfigure(encoding='utf-8')

for p in sorted(glob.glob(r"targets\district-187\client-rebirth\DevLog\*"), key=os.path.getmtime)[-6:]:
    print(f"=== {p} (size={os.path.getsize(p)}) ===")
    with open(p, "rb") as f:
        print(f.read().decode("cp949", errors="replace")[-2000:])
