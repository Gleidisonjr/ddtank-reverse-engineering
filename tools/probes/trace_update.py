import ctypes
from ctypes import wintypes
import subprocess
import time
import os
import sys

kernel32 = ctypes.windll.kernel32

def trace_update():
    subprocess.run(["taskkill", "/f", "/im", "TheRaw.exe"], capture_output=True)
    time.sleep(1)

    client_dir = os.path.abspath(r"targets\district-187\client-rebirth")
    exe = os.path.join(client_dir, "TheRaw.exe")
    cmd = f'"{exe}" -arch game -archcfg Default.archcfg -windowtitle "District 187: Sin Streets" +gs_ip 127.0.0.1 +gs_port 12000 +windowed 1 +ScreenWidth 1920 +ScreenHeight 1080'

    class STARTUPINFO(ctypes.Structure):
        _fields_ = [('cb', wintypes.DWORD), ('lpReserved', wintypes.LPWSTR),
                    ('lpDesktop', wintypes.LPWSTR), ('lpTitle', wintypes.LPWSTR),
                    ('dwX', wintypes.DWORD), ('dwY', wintypes.DWORD),
                    ('dwXSize', wintypes.DWORD), ('dwYSize', wintypes.DWORD),
                    ('dwXCountChars', wintypes.DWORD), ('dwYCountChars', wintypes.DWORD),
                    ('dwFillAttribute', wintypes.DWORD), ('dwFlags', wintypes.DWORD),
                    ('wShowWindow', wintypes.WORD), ('cbReserved2', wintypes.WORD),
                    ('lpReserved2', ctypes.c_char_p), ('hStdInput', wintypes.HANDLE),
                    ('hStdOutput', wintypes.HANDLE), ('hStdError', wintypes.HANDLE)]

    class PROCESS_INFORMATION(ctypes.Structure):
        _fields_ = [('hProcess', wintypes.HANDLE), ('hThread', wintypes.HANDLE),
                    ('dwProcessId', wintypes.DWORD), ('dwThreadId', wintypes.DWORD)]

    si = STARTUPINFO()
    si.cb = ctypes.sizeof(si)
    pi = PROCESS_INFORMATION()

    os.environ["__COMPAT_LAYER"] = "RunAsInvoker"
    cur = os.getcwd()
    os.chdir(client_dir)
    res = kernel32.CreateProcessW(None, cmd, None, None, False, 1, None, None, ctypes.byref(si), ctypes.byref(pi))
    os.chdir(cur)
    if not res:
        print("CreateProcess failed", flush=True)
        return

    print(f"[+] Started PID {pi.dwProcessId}", flush=True)
    hp = pi.hProcess

    bps = {
        0x00490eec: "ShowWindow",
        0x00490f13: "Call ClientApp::Update",
        0x00490f18: "After ClientApp::Update",
        0x00490f64: "Check [0x84ec25]",
        0x00490f6c: "Set exit code from [0x84ec28]",
        0x00490f74: "Main Loop Exit Routine"
    }

    orig = {}
    for a in bps:
        b = ctypes.c_byte()
        kernel32.ReadProcessMemory(hp, a, ctypes.byref(b), 1, None)
        orig[a] = bytes(b)
        int3 = ctypes.c_char(b'\xcc')
        kernel32.WriteProcessMemory(hp, a, ctypes.byref(int3), 1, None)

    class WOW64_CONTEXT(ctypes.Structure):
        _fields_ = [
            ('ContextFlags', wintypes.DWORD),
            ('Dr0', wintypes.DWORD), ('Dr1', wintypes.DWORD), ('Dr2', wintypes.DWORD), ('Dr3', wintypes.DWORD),
            ('Dr6', wintypes.DWORD), ('Dr7', wintypes.DWORD),
            ('FloatSave', ctypes.c_byte * 112),
            ('SegGs', wintypes.DWORD), ('SegFs', wintypes.DWORD), ('SegEs', wintypes.DWORD), ('SegDs', wintypes.DWORD),
            ('Edi', wintypes.DWORD), ('Esi', wintypes.DWORD), ('Ebx', wintypes.DWORD), ('Edx', wintypes.DWORD),
            ('Ecx', wintypes.DWORD), ('Eax', wintypes.DWORD), ('Ebp', wintypes.DWORD), ('Eip', wintypes.DWORD),
            ('SegCs', wintypes.DWORD), ('EFlags', wintypes.DWORD), ('Esp', wintypes.DWORD), ('SegSs', wintypes.DWORD),
            ('ExtendedRegisters', ctypes.c_byte * 512),
        ]

    class DEBUG_EVENT(ctypes.Structure):
        class _U(ctypes.Union):
            _fields_ = [('Exception', ctypes.c_byte * 160)]
        _fields_ = [
            ('dwDebugEventCode', wintypes.DWORD),
            ('dwProcessId', wintypes.DWORD),
            ('dwThreadId', wintypes.DWORD),
            ('u', _U)
        ]

    evt = DEBUG_EVENT()
    frame_count = 0
    while True:
        if not kernel32.WaitForDebugEvent(ctypes.byref(evt), 5000):
            print("[!] Timeout", flush=True)
            break

        code = evt.dwDebugEventCode
        if code == 1:
            rec = ctypes.cast(evt.u.Exception, ctypes.POINTER(wintypes.DWORD))
            if rec[0] == 0x80000003 and rec[3] in bps:
                addr = rec[3]
                name = bps[addr]
                ht = kernel32.OpenThread(0x001F03FF, False, evt.dwThreadId)
                ctx = WOW64_CONTEXT()
                ctx.ContextFlags = 0x10007
                kernel32.Wow64GetThreadContext(ht, ctypes.byref(ctx))

                if name == "Call ClientApp::Update":
                    frame_count += 1
                    if frame_count <= 3 or frame_count % 30 == 0:
                        print(f"[FRAME {frame_count}] Calling ClientApp::Update", flush=True)
                elif name == "After ClientApp::Update":
                    if ctx.Eax != 0 or frame_count <= 3:
                        print(f"[FRAME {frame_count}] ClientApp::Update returned: {ctx.Eax}", flush=True)
                else:
                    print(f"[BP] {name} (EAX=0x{ctx.Eax:x}, EBX=0x{ctx.Ebx:x})", flush=True)

                ctx.Eip = addr
                ctx.EFlags |= 0x100
                kernel32.Wow64SetThreadContext(ht, ctypes.byref(ctx))
                kernel32.WriteProcessMemory(hp, addr, orig[addr], 1, None)
                kernel32.CloseHandle(ht)
                kernel32.ContinueDebugEvent(evt.dwProcessId, evt.dwThreadId, 0x00010002)
                continue

            elif rec[0] == 0x80000004:
                for a in bps:
                    int3 = ctypes.c_char(b'\xcc')
                    kernel32.WriteProcessMemory(hp, a, ctypes.byref(int3), 1, None)
                kernel32.ContinueDebugEvent(evt.dwProcessId, evt.dwThreadId, 0x00010002)
                continue

        elif code == 5:
            print("[+] Process exited cleanly.", flush=True)
            break

        kernel32.ContinueDebugEvent(evt.dwProcessId, evt.dwThreadId, 0x00010002)

if __name__ == "__main__":
    trace_update()
