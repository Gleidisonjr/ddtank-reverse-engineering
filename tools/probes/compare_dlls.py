import glob, os

for name in ['DxBase.dll', 'dbbase.dll', 'strbase.dll', 'GameDatabase.dll', 'StringEditRuntime.dll']:
    p1 = os.path.join(r'targets/district-187/client/S2', name)
    p2 = os.path.join(r'targets/district-187/client-rebirth', name)
    if os.path.exists(p1) and os.path.exists(p2):
        d1 = open(p1, 'rb').read()
        d2 = open(p2, 'rb').read()
        diffs = sum(1 for a, b in zip(d1, d2) if a != b) + abs(len(d1) - len(d2))
        print(f"{name}: diff bytes = {diffs} (len1={len(d1)}, len2={len(d2)})")
    else:
        print(f"{name}: missing in one of the locations")
