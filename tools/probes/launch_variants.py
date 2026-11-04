import os, subprocess, time, sys
d = r"C:\Users\dopamine\Desktop\Projetos\Reverse Engineering\targets\district-187\client-rebirth"
variants = {
  "A bat-exact title": ["-arch","game","-windowtitle","District 187: Sin Streets (Ultra HD)","+gs_ip","127.0.0.1","+gs_port","12000"],
  "B no args": [],
  "C arch only": ["-arch","game"],
}
for name, args in variants.items():
    env = dict(os.environ, __COMPAT_LAYER="RunAsInvoker")
    p = subprocess.Popen([os.path.join(d,"TheRaw.exe")]+args, cwd=d, env=env)
    t0=time.time()
    while time.time()-t0 < 12 and p.poll() is None:
        time.sleep(0.5)
    rc = p.poll()
    print(name, "-> exited rc=%s after %.1fs" % (rc, time.time()-t0) if rc is not None else "-> STILL RUNNING after 12s")
    if rc is None:
        p.kill(); break
    time.sleep(1)
