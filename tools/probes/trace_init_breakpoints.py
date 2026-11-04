import os
import sys
import time
import subprocess
import ctypes
from ctypes import wintypes

kernel32 = ctypes.windll.kernel32

client_dir = os.path.abspath(r"targets\district-187\client-rebirth")
exe_path = os.path.join(client_dir, "TheRaw.exe")
cmd = f'"{exe_path}" -arch game -archcfg Default.archcfg -windowtitle "District 187: Sin Streets" +gs_ip 127.0.0.1 +gs_port 12000 +windowed 1 +ScreenWidth 1920 +ScreenHeight 1080'

os.environ["__COMPAT_LAYER"] = "RunAsInvoker"
subprocess.run(["taskkill", "/f", "/im", "TheRaw.exe"], capture_output=True)
time.sleep(1)

class STARTUPINFO(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("lpReserved", wintypes.LPSTR),
        ("lpDesktop", wintypes.LPSTR),
        ("lpTitle", wintypes.LPSTR),
        ("dwX", wintypes.DWORD),
        ("dwY", wintypes.DWORD),
        ("dwXSize", wintypes.DWORD),
        ("dwYSize", wintypes.DWORD),
        ("dwXCountChars", wintypes.DWORD),
        ("dwYCountChars", wintypes.DWORD),
        ("dwFillAttribute", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("wShowWindow", wintypes.WORD),
        ("cbReserved2", wintypes.WORD),
        ("lpReserved2", ctypes.c_void_p),
        ("hStdInput", wintypes.HANDLE),
        ("hStdOutput", wintypes.HANDLE),
        ("hStdError", wintypes.HANDLE),
    ]

class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("hProcess", wintypes.HANDLE),
        ("hThread", wintypes.HANDLE),
        ("dwProcessId", wintypes.DWORD),
        ("dwThreadId", wintypes.DWORD),
    ]

class DEBUG_EVENT(ctypes.Structure):
    class _u(ctypes.Union):
        class EXCEPTION_DEBUG_INFO(ctypes.Structure):
            class EXCEPTION_RECORD(ctypes.Structure):
                pass
            EXCEPTION_RECORD._fields_ = [
                ("ExceptionCode", wintypes.DWORD),
                ("ExceptionFlags", wintypes.DWORD),
                ("ExceptionRecord", ctypes.POINTER(EXCEPTION_RECORD)),
                ("ExceptionAddress", ctypes.c_void_p),
                ("NumberParameters", wintypes.DWORD),
                ("ExceptionInformation", ctypes.c_size_t * 15),
            ]
            _fields_ = [
                ("ExceptionRecord", EXCEPTION_RECORD),
                ("dwFirstChance", wintypes.DWORD),
            ]

        class CREATE_THREAD_DEBUG_INFO(ctypes.Structure):
            _fields_ = [
                ("hThread", wintypes.HANDLE),
                ("lpThreadLocalBase", ctypes.c_void_p),
                ("lpStartAddress", ctypes.c_void_p),
            ]

        class CREATE_PROCESS_DEBUG_INFO(ctypes.Structure):
            _fields_ = [
                ("hFile", wintypes.HANDLE),
                ("hProcess", wintypes.HANDLE),
                ("hThread", wintypes.HANDLE),
                ("lpBaseOfImage", ctypes.c_void_p),
                ("dwDebugInfoFileOffset", wintypes.DWORD),
                ("nDebugInfoSize", wintypes.DWORD),
                ("lpThreadLocalBase", ctypes.c_void_p),
                ("lpStartAddress", ctypes.c_void_p),
                ("lpImageName", ctypes.c_void_p),
                ("fUnicode", wintypes.WORD),
            ]

        class EXIT_THREAD_DEBUG_INFO(ctypes.Structure):
            _fields_ = [("dwExitCode", wintypes.DWORD)]

        class EXIT_PROCESS_DEBUG_INFO(ctypes.Structure):
            _fields_ = [("dwExitCode", wintypes.DWORD)]

        class LOAD_DLL_DEBUG_INFO(ctypes.Structure):
            _fields_ = [
                ("hFile", wintypes.HANDLE),
                ("lpBaseOfDll", ctypes.c_void_p),
                ("dwDebugInfoFileOffset", wintypes.DWORD),
                ("nDebugInfoSize", wintypes.DWORD),
                ("lpImageName", ctypes.c_void_p),
                ("fUnicode", wintypes.WORD),
            ]

        class UNLOAD_DLL_DEBUG_INFO(ctypes.Structure):
            _fields_ = [("lpBaseOfDll", ctypes.c_void_p)]

        class OUTPUT_DEBUG_STRING_INFO(ctypes.Structure):
            _fields_ = [
                ("lpDebugStringData", ctypes.c_char_p),
                ("fUnicode", wintypes.WORD),
                ("nDebugStringLength", wintypes.WORD),
            ]

        class RIP_INFO(ctypes.Structure):
            _fields_ = [
                ("dwError", wintypes.DWORD),
                ("dwType", wintypes.DWORD),
            ]

        _fields_ = [
            ("Exception", EXCEPTION_DEBUG_INFO),
            ("CreateThread", CREATE_THREAD_DEBUG_INFO),
            ("CreateProcessInfo", CREATE_PROCESS_DEBUG_INFO),
            ("ExitThread", EXIT_THREAD_DEBUG_INFO),
            ("ExitProcess", EXIT_PROCESS_DEBUG_INFO),
            ("LoadDll", LOAD_DLL_DEBUG_INFO),
            ("UnloadDll", UNLOAD_DLL_DEBUG_INFO),
            ("DebugString", OUTPUT_DEBUG_STRING_INFO),
            ("RipInfo", RIP_INFO),
        ]

    _fields_ = [
        ("dwDebugEventCode", wintypes.DWORD),
        ("dwProcessId", wintypes.DWORD),
        ("dwThreadId", wintypes.DWORD),
        ("u", _u),
    ]

si = STARTUPINFO()
si.cb = ctypes.sizeof(STARTUPINFO)
pi = PROCESS_INFORMATION()

DEBUG_ONLY_THIS_PROCESS = 0x00000002

success = kernel32.CreateProcessA(
    None,
    cmd.encode("latin1"),
    None, None, False,
    DEBUG_ONLY_THIS_PROCESS,
    None,
    client_dir.encode("latin1"),
    ctypes.byref(si),
    ctypes.byref(pi)
)

if not success:
    print(f"[-] CreateProcess failed: {kernel32.GetLastError()}")
    sys.exit(1)

print(f"[+] Started PID {pi.dwProcessId} under debugger.")

breakpoints = {
    0x004c34af: "Direct3D9: CheckDeviceType Call",
    0x004c34b2: "Direct3D9: CheckDeviceType After",
    0x004c2075: "Renderer: FindMode entry",
    0x004be31f: "Renderer: Check FindMode result",
    0x004c0deb: "Direct3D9: CreateDevice Call",
    0x004c0dee: "Direct3D9: CreateDevice After",
    0x004c0e2b: "Direct3D9: CreateDevice Call #2 (Fallback)",
    0x004c0e2e: "Direct3D9: CreateDevice After #2",
    0x004c0e89: "Renderer: CreateDevice SUCCESS (al = 1)",
    0x004c0e8d: "Renderer: CreateDevice FAIL (MessageBox)"
}

original_bytes = {}
hProcess = pi.hProcess

def set_bp(addr):
    old_protect = wintypes.DWORD()
    kernel32.VirtualProtectEx(hProcess, ctypes.c_void_p(addr), 1, 0x40, ctypes.byref(old_protect))
    b = ctypes.c_char()
    read = ctypes.c_size_t()
    kernel32.ReadProcessMemory(hProcess, ctypes.c_void_p(addr), ctypes.byref(b), 1, ctypes.byref(read))
    original_bytes[addr] = b.value
    int3 = b"\xcc"
    kernel32.WriteProcessMemory(hProcess, ctypes.c_void_p(addr), int3, 1, ctypes.byref(read))
    kernel32.VirtualProtectEx(hProcess, ctypes.c_void_p(addr), 1, old_protect.value, ctypes.byref(old_protect))

def restore_byte(addr):
    if addr in original_bytes:
        old_protect = wintypes.DWORD()
        kernel32.VirtualProtectEx(hProcess, ctypes.c_void_p(addr), 1, 0x40, ctypes.byref(old_protect))
        b = original_bytes[addr]
        read = ctypes.c_size_t()
        kernel32.WriteProcessMemory(hProcess, ctypes.c_void_p(addr), b, 1, ctypes.byref(read))
        kernel32.VirtualProtectEx(hProcess, ctypes.c_void_p(addr), 1, old_protect.value, ctypes.byref(old_protect))

# Set bps for TheRaw right away
for addr in breakpoints:
    if addr < 0x10000000:
        set_bp(addr)

game_client_base = None
debug_event = DEBUG_EVENT()
DBG_CONTINUE = 0x00010002
DBG_EXCEPTION_NOT_HANDLED = 0x80010001

start_time = time.time()
while time.time() - start_time < 15:
    if not kernel32.WaitForDebugEvent(ctypes.byref(debug_event), 500):
        continue

    code = debug_event.dwDebugEventCode
    pid = debug_event.dwProcessId
    tid = debug_event.dwThreadId

    status = DBG_CONTINUE

    if code == 6: # LOAD_DLL
        lpBase = debug_event.u.LoadDll.lpBaseOfDll
        # check if GameClient.dll
        # read PE header to find export or name
        if lpBase == 0x10000000:
            print(f"[+] GameClient.dll loaded at {hex(lpBase)}")
            game_client_base = lpBase
            for addr in breakpoints:
                if addr >= 0x10000000:
                    set_bp(addr)
    elif code == 1: # EXCEPTION
        exc = debug_event.u.Exception
        exc_code = exc.ExceptionRecord.ExceptionCode
        exc_addr = exc.ExceptionRecord.ExceptionAddress
        if exc_code in (0x80000003, 0x4000001f): # STATUS_BREAKPOINT or STATUS_WX86_BREAKPOINT
            if exc_addr in breakpoints:
                desc = breakpoints[exc_addr]
                print(f"[BREAKPOINT] HIT: {hex(exc_addr)} -> {desc}")
                # Restore original byte
                restore_byte(exc_addr)
                # Rewind EIP by 1
                hThread = kernel32.OpenThread(0x001F03FF, False, tid)
                if hThread:
                    class WOW64_CONTEXT(ctypes.Structure):
                        _fields_ = [
                            ("ContextFlags", wintypes.DWORD),
                            ("Dr0", wintypes.DWORD), ("Dr1", wintypes.DWORD), ("Dr2", wintypes.DWORD),
                            ("Dr3", wintypes.DWORD), ("Dr6", wintypes.DWORD), ("Dr7", wintypes.DWORD),
                            ("FloatSave", wintypes.BYTE * 112),
                            ("SegGs", wintypes.DWORD), ("SegFs", wintypes.DWORD), ("SegEs", wintypes.DWORD),
                            ("SegDs", wintypes.DWORD),
                            ("Edi", wintypes.DWORD), ("Esi", wintypes.DWORD), ("Ebx", wintypes.DWORD),
                            ("Edx", wintypes.DWORD), ("Ecx", wintypes.DWORD), ("Eax", wintypes.DWORD),
                            ("Ebp", wintypes.DWORD), ("Eip", wintypes.DWORD), ("SegCs", wintypes.DWORD),
                            ("EFlags", wintypes.DWORD), ("Esp", wintypes.DWORD), ("SegSs", wintypes.DWORD),
                            ("ExtendedRegisters", wintypes.BYTE * 512),
                        ]
                    ctx = WOW64_CONTEXT()
                    ctx.ContextFlags = 0x10007 # CONTEXT_CONTROL | CONTEXT_INTEGER
                    if hasattr(kernel32, "Wow64GetThreadContext"):
                        kernel32.Wow64GetThreadContext(hThread, ctypes.byref(ctx))
                    else:
                        kernel32.GetThreadContext(hThread, ctypes.byref(ctx))
                    print(f"    EAX={hex(ctx.Eax)} EBX={hex(ctx.Ebx)} ECX={hex(ctx.Ecx)} EDX={hex(ctx.Edx)} ESI={hex(ctx.Esi)} EDI={hex(ctx.Edi)} ESP={hex(ctx.Esp)} EIP={hex(ctx.Eip)}")
                    if exc_addr == 0x004c2075:
                        # Stack: ret, dev_ptr, width, height, bpp, byte_flag, bool_flag
                        params = (wintypes.DWORD * 7)()
                        read = ctypes.c_size_t()
                        kernel32.ReadProcessMemory(hProcess, ctypes.c_void_p(ctx.Esp), ctypes.byref(params), 28, ctypes.byref(read))
                        dev = params[1]
                        req_w = params[2]
                        req_h = params[3]
                        req_bpp = params[4]
                        flag1 = params[5]
                        flag2 = params[6]
                        print(f"    [0x4c2075] Dev: {hex(dev)}, Req: {req_w}x{req_h} ({req_bpp}bpp), flags: {flag1}, {flag2}")
                        # Read dev mode list: dev+0x13c (start), dev+0x140 (end)
                        bounds = (wintypes.DWORD * 2)()
                        kernel32.ReadProcessMemory(hProcess, ctypes.c_void_p(dev + 0x13c), ctypes.byref(bounds), 8, ctypes.byref(read))
                        start_addr = bounds[0]
                        end_addr = bounds[1]
                        count = (end_addr - start_addr) // 16
                        print(f"    [0x4c2075] Modes bounds: {hex(start_addr)} to {hex(end_addr)} (Count: {count})")
                        modes_raw = (wintypes.DWORD * (count * 4))()
                        kernel32.ReadProcessMemory(hProcess, ctypes.c_void_p(start_addr), ctypes.byref(modes_raw), count * 16, ctypes.byref(read))
                        for idx in range(count):
                            w = modes_raw[idx*4 + 0]
                            h = modes_raw[idx*4 + 1]
                            fmt = modes_raw[idx*4 + 2]
                            flags = modes_raw[idx*4 + 3]
                            print(f"       Mode {idx:02d}: {w}x{h}, fmt={hex(fmt)}, flags={hex(flags)}")
                    if exc_addr == 0x004c3674:
                        # ESI = this (0x861078), ESI+4 = D3DADAPTER_IDENTIFIER9
                        buf = (ctypes.c_char * 1024)()
                        read = ctypes.c_size_t()
                        kernel32.ReadProcessMemory(hProcess, ctypes.c_void_p(ctx.Esi + 4), ctypes.byref(buf), 1024, ctypes.byref(read))
                        driver = buf.raw[:512].split(b'\x00')[0].decode('latin1', errors='ignore')
                        desc = buf.raw[512:1024].split(b'\x00')[0].decode('latin1', errors='ignore')
                        print(f"    Adapter 0: Driver={repr(driver)}, Desc={repr(desc)}")
                    if exc_addr in (0x004c0deb, 0x004c0e2b):
                        # Stack: this, adapter, devtype, focus_hwnd, behavior_flags, pparams, out_device
                        params = (wintypes.DWORD * 7)()
                        read = ctypes.c_size_t()
                        kernel32.ReadProcessMemory(hProcess, ctypes.c_void_p(ctx.Esp), ctypes.byref(params), 28, ctypes.byref(read))
                        devtype = params[2]
                        focus_hwnd = params[3]
                        flags = params[4]
                        pp_ptr = params[5]
                        pp = (wintypes.DWORD * 14)()
                        kernel32.ReadProcessMemory(hProcess, ctypes.c_void_p(pp_ptr), ctypes.byref(pp), 56, ctypes.byref(read))
                        print(f"    CreateDevice args: Adapter={params[1]}, DevType={devtype}, FocusHWND={hex(focus_hwnd)}, Flags={hex(flags)}, PP_ptr={hex(pp_ptr)}")
                        print(f"       D3DPRESENT_PARAMETERS: Width={pp[0]}, Height={pp[1]}, Fmt={hex(pp[2])}, BBCount={pp[3]}, MSType={pp[4]}, MSQual={pp[5]}, SwapEffect={pp[6]}, WinHwnd={hex(pp[7])}, Windowed={pp[8]}, AutoDS={pp[9]}, DSFormat={hex(pp[10])}, Flags={hex(pp[11])}, Refresh={pp[12]}, Interval={hex(pp[13])}")
                    if exc_addr in (0x004c0dee, 0x004c0e2e):
                        print(f"    CreateDevice returned HRESULT: {hex(ctx.Eax & 0xffffffff)}")
                    if exc_addr == 0x004c34af:
                        # Stack: ret, this, adapter, devtype, disp_fmt, bb_fmt, windowed
                        one = wintypes.DWORD(1)
                        read = ctypes.c_size_t()
                        kernel32.WriteProcessMemory(hProcess, ctypes.c_void_p(ctx.Esp + 20), ctypes.byref(one), 4, ctypes.byref(read))
                        params = (wintypes.DWORD * 7)()
                        kernel32.ReadProcessMemory(hProcess, ctypes.c_void_p(ctx.Esp), ctypes.byref(params), 28, ctypes.byref(read))
                        print(f"    CheckDeviceType args: Adapter={params[1]}, DevType={params[2]}, DispFmt={hex(params[3])}, BBFmt={hex(params[4])}, Windowed={params[5]}")
                    if exc_addr == 0x004c34b2:
                        print(f"    CheckDeviceType returned HRESULT: {hex(ctx.Eax & 0xffffffff)}")
                    ctx.Eip -= 1
                    if hasattr(kernel32, "Wow64SetThreadContext"):
                        kernel32.Wow64SetThreadContext(hThread, ctypes.byref(ctx))
                    else:
                        kernel32.SetThreadContext(hThread, ctypes.byref(ctx))
                    kernel32.CloseHandle(hThread)
            else:
                # System breakpoint (initial breakpoint)
                status = DBG_CONTINUE
        else:
            if exc_code != 0xe06d7363:
                print(f"[!] Exception {hex(exc_code)} at {hex(exc_addr)}")
            status = DBG_EXCEPTION_NOT_HANDLED
    elif code == 5: # EXIT_PROCESS
        print(f"[*] Process exited with code {debug_event.u.ExitProcess.dwExitCode}")
        kernel32.ContinueDebugEvent(pid, tid, DBG_CONTINUE)
        break

    kernel32.ContinueDebugEvent(pid, tid, status)

kernel32.CloseHandle(pi.hProcess)
kernel32.CloseHandle(pi.hThread)
