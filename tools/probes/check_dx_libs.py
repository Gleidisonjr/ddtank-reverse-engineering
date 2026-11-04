import os, hashlib, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
base = r"C:\Users\dopamine\Desktop\Projetos\Reverse Engineering\targets\district-187"
def h(p):
    return hashlib.sha256(open(p,'rb').read()).hexdigest()[:16] if os.path.exists(p) else None
cands = {
 "rebirth/D3DX9_43.dll": base+r"\client-rebirth\D3DX9_43.dll",
 "rebirth/Game/D3DX9_43.dll": base+r"\client-rebirth\Game\D3DX9_43.dll",
 "community/D3DX9_43.dll": base+r"\client\S2\D3DX9_43.dll",
 "SysWOW64/d3dx9_43.dll": r"C:\Windows\SysWOW64\d3dx9_43.dll",
}
for k, v in cands.items():
    print(f"{k:30} exists={os.path.exists(v)} size={os.path.getsize(v) if os.path.exists(v) else '-'} sha={h(v)}")
print("\n-- dx-ish files in client-rebirth --")
root = base + r"\client-rebirth"
for dp, dn, fn in os.walk(root):
    if 'Worlds' in dp or 'HD' in dp: continue
    for f in fn:
        if f.lower().startswith(('d3d','dxgi','xinput','d3dcompiler')) or 'apex' in f.lower():
            p = os.path.join(dp, f); print(os.path.relpath(p, root), os.path.getsize(p), h(p))
