import ctypes
from ctypes import wintypes
import subprocess
import time
import os

DEBUG_PROCESS = 0x00000001
CREATE_SUSPENDED = 0x00000004
DBG_CONTINUE = 0x00010002
EXCEPTION_DEBUG_EVENT = 1
CREATE_PROCESS_DEBUG_EVENT = 3
EXIT_PROCESS_DEBUG_EVENT = 5
LOAD_DLL_DEBUG_EVENT = 6

class DEBUG_EVENT(ctypes.Structure):
    class _U(ctypes.Union):
        _fields_ = [('Exception', ctypes.c_byte * 160),
                    ('CreateProcessInfo', ctypes.c_byte * 160),
                    ('LoadDll', ctypes.c_byte * 160),
                    ('ExitProcess', ctypes.c_byte * 160)]
    _fields_ = [
        ('dwDebugEventCode', wintypes.DWORD),
        ('dwProcessId', wintypes.DWORD),
        ('dwThreadId', wintypes.DWORD),
        ('u', _U)
    ]

kernel32 = ctypes.windll.kernel32

def trace_loop():
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
    curdir = os.getcwd()
    os.chdir(client_dir)

    success = kernel32.CreateProcessW(
        None, cmd, None, None, False, DEBUG_PROCESS, None, None, ctypes.byref(si), ctypes.byref(pi)
    )
    os.chdir(curdir)

    if not success:
        print("CreateProcess failed:", kernel32.GetLastError())
        return

    print(f"[+] Started TheRaw.exe PID {pi.dwProcessId}")
    hProcess = pi.hProcess

    breakpoints = {
        0x00490eec: "Before ShowWindow",
        0x00490ef2: "After ShowWindow",
        0x00490ef5: "After UpdateWindow",
        0x00490f13: "Call ClientApp::Update",
        0x00490f18: "After ClientApp::Update",
        0x00490f64: "Check [0x84ec25]",
        0x00490f74: "Main Loop Exit Routine",
        0x004926fd: "Engine Error Reporter"
    }

    orig_bytes = {}
    for addr in breakpoints:
        old_b = ctypes.c_byte()
        kernel32.ReadProcessMemory(hProcess, addr, ctypes.byref(old_b), 1, None)
        orig_bytes[addr] = bytes(old_b)
        int3 = ctypes.c_char(b'\xcc')
        kernel32.WriteProcessMemory(hProcess, addr, ctypes.byref(int3), 1, None)

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

    evt = DEBUG_EVENT()
    update_count = 0
    while True:
        if not kernel32.WaitForDebugEvent(ctypes.byref(evt), 5000):
            print("[!] Timeout in WaitForDebugEvent")
            break

        code = evt.dwDebugEventCode
        if code == EXCEPTION_DEBUG_EVENT:
            record = ctypes.cast(evt.u.Exception, ctypes.POINTER(wintypes.DWORD))
            exc_code = record[0]
            exc_addr = record[3]

            if exc_code == 0x80000003 and exc_addr in breakpoints:
                name = breakpoints[exc_addr]
                hThread = kernel32.OpenThread(0x001F03FF, False, evt.dwThreadId)
                ctx = WOW64_CONTEXT()
                ctx.ContextFlags = 0x10007
                kernel32.Wow64GetThreadContext(hThread, ctypes.byref(ctx))

                # Step over BP
                ctx.Eip = exc_addr
                ctx.EFlags |= 0x100 # Single-step
                kernel32.Wow64SetThreadContext(hThread, ctypes.byref(ctx))
                kernel32.WriteProcessMemory(hProcess, exc_addr, orig_bytes[exc_addr], 1, None)

                if name == "Call ClientApp::Update":
                    update_count += 1
                    if update_count <= 5 or update_count % 50 == 0:
                        print(f"[BP] {name} #{update_count} (EAX=0x{ctx.Eax:x})")
                elif name == "After ClientApp::Update":
                    if update_count <= 5 or ctx.Eax != 0:
                        print(f"[BP] {name} (Returned EAX={ctx.Eax})")
                else:
                    print(f"[BP] Hit: {name} (EAX=0x{ctx.Eax:x}, EBX=0x{ctx.Ebx:x})")

                kernel32.CloseHandle(hThread)
                kernel32.ContinueDebugEvent(evt.dwProcessId, evt.dwThreadId, DBG_CONTINUE)
                continue

            elif exc_code == 0x80000004: # SINGLE_STEP
                # Restore INT3
                for addr in breakpoints:
                    int3 = ctypes.c_char(b'\xcc')
                    kernel32.WriteProcessMemory(hProcess, addr, ctypes.byref(int3), 1, None)
                kernel32.ContinueDebugEvent(evt.dwProcessId, evt.dwThreadId, DBG_CONTINUE)
                continue

        elif code == EXIT_PROCESS_DEBUG_EVENT:
            print("[+] Process exited cleanly!")
            break

        kernel32.ContinueDebugEvent(evt.dwProcessId, evt.dwThreadId, DBG_CONTINUE)

if __name__ == "__main__":
    trace_loop()
