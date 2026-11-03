import os, subprocess, time, psutil, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
d = r"C:\Users\dopamine\Desktop\Projetos\Reverse Engineering\targets\district-187\client-rebirth"
env = dict(os.environ, __COMPAT_LAYER="RunAsInvoker")
p = subprocess.Popen([os.path.join(d, "TheRaw.exe"), "-arch", "game", "-windowtitle", "D187",
                      "+gs_ip", "127.0.0.1", "+gs_port", "12000"], cwd=d, env=env)
print("pid", p.pid)
for i in range(12):
    time.sleep(2)
    rc = p.poll()
    conns = [(c.laddr.port, c.status) for c in psutil.net_connections('tcp') if c.pid == p.pid]
    print(i * 2 + 2, "s rc=", rc, conns)
    if rc is not None:
        break
