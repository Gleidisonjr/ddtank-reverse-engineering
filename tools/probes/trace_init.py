import ctypes
from ctypes import wintypes
import os
import sys

kernel32 = ctypes.windll.kernel32
kernel32.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
kernel32.WriteProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
kernel32.FlushInstructionCache.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_size_t]

DEBUG_PROCESS = 0x00000001
DBG_CONTINUE = 0x00010002
DBG_EXCEPTION_NOT_HANDLED = 0x80010001

EXCEPTION_DEBUG_EVENT = 1
CREATE_THREAD_DEBUG_EVENT = 2
CREATE_PROCESS_DEBUG_EVENT = 3
EXIT_THREAD_DEBUG_EVENT = 4
EXIT_PROCESS_DEBUG_EVENT = 5
LOAD_DLL_DEBUG_EVENT = 6
UNLOAD_DLL_DEBUG_EVENT = 7
OUTPUT_DEBUG_STRING_EVENT = 8
RIP_EVENT = 9

class STARTUPINFO(ctypes.Structure):
    _fields_ = [
        ('cb', wintypes.DWORD),
        ('lpReserved', wintypes.LPWSTR),
        ('lpDesktop', wintypes.LPWSTR),
        ('lpTitle', wintypes.LPWSTR),
        ('dwX', wintypes.DWORD),
        ('dwY', wintypes.DWORD),
        ('dwXSize', wintypes.DWORD),
        ('dwYSize', wintypes.DWORD),
        ('dwXCountChars', wintypes.DWORD),
        ('dwYCountChars', wintypes.DWORD),
        ('dwFillAttribute', wintypes.DWORD),
        ('dwFlags', wintypes.DWORD),
        ('wShowWindow', wintypes.WORD),
        ('cbReserved2', wintypes.WORD),
        ('lpReserved2', ctypes.c_char_p),
        ('hStdInput', wintypes.HANDLE),
        ('hStdOutput', wintypes.HANDLE),
        ('hStdError', wintypes.HANDLE),
    ]

class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ('hProcess', wintypes.HANDLE),
        ('hThread', wintypes.HANDLE),
        ('dwProcessId', wintypes.DWORD),
        ('dwThreadId', wintypes.DWORD),
    ]

class EXCEPTION_RECORD(ctypes.Structure):
    pass
EXCEPTION_RECORD._fields_ = [
    ('ExceptionCode', wintypes.DWORD),
    ('ExceptionFlags', wintypes.DWORD),
    ('pExceptionRecord', ctypes.POINTER(EXCEPTION_RECORD)),
    ('ExceptionAddress', ctypes.c_void_p),
    ('NumberParameters', wintypes.DWORD),
    ('ExceptionInformation', ctypes.c_ulong * 15),
]

class EXCEPTION_DEBUG_INFO(ctypes.Structure):
    _fields_ = [
        ('ExceptionRecord', EXCEPTION_RECORD),
        ('dwFirstChance', wintypes.DWORD),
    ]

class LOAD_DLL_DEBUG_INFO(ctypes.Structure):
    _fields_ = [
        ('hFile', wintypes.HANDLE),
        ('lpBaseOfDll', ctypes.c_void_p),
        ('dwDebugInfoFileOffset', wintypes.DWORD),
        ('nDebugInfoSize', wintypes.DWORD),
        ('lpImageName', ctypes.c_void_p),
        ('fUnicode', wintypes.WORD),
    ]

class DEBUG_EVENT_UNION(ctypes.Union):
    _fields_ = [
        ('Exception', EXCEPTION_DEBUG_INFO),
        ('LoadDll', LOAD_DLL_DEBUG_INFO),
        ('raw', ctypes.c_byte * 160),
    ]

class DEBUG_EVENT(ctypes.Structure):
    _fields_ = [
        ('dwDebugEventCode', wintypes.DWORD),
        ('dwProcessId', wintypes.DWORD),
        ('dwThreadId', wintypes.DWORD),
        ('u', DEBUG_EVENT_UNION),
    ]

def main():
    si = STARTUPINFO()
    si.cb = ctypes.sizeof(si)
    pi = PROCESS_INFORMATION()

    os.environ["__COMPAT_LAYER"] = "RunAsInvoker"
    client_dir = r"C:\Users\dopamine\Desktop\Projetos\Reverse Engineering\targets\district-187\client-rebirth"
    exe = os.path.join(client_dir, "TheRaw.exe")
    cmd = f'"{exe}" -arch game -windowtitle "District 187: Sin Streets" +gs_ip 127.0.0.1 +gs_port 12000 +windowed 1 +ScreenWidth 1920 +ScreenHeight 1080 +ShowLog 1'

    # Terminate any hung TheRaw.exe
    os.system("taskkill /f /im TheRaw.exe >nul 2>&1")

    res = kernel32.CreateProcessW(
        None,
        cmd,
        None,
        None,
        False,
        DEBUG_PROCESS,
        None,
        client_dir,
        ctypes.byref(si),
        ctypes.byref(pi),
    )
    if not res:
        print("CreateProcess failed:", kernel32.GetLastError())
        return

    print(f"[+] Started TheRaw.exe PID {pi.dwProcessId} under debugger")

    game_client_base = None
    breakpoints = {}
    orig_bytes = {}

    the_raw_base = 0x400000
    points_to_set = {
        0x23b0dd: ("Call 0x100a6350 (Game Init)", "gc"),
        0x23b1b7: ("Call ILTClient->SetRenderMode", "gc"),
        0x23b1c0: ("FAIL SetRenderMode -> Exit 1", "gc"),
        0xc0deb:  ("Call IDirect3D9::CreateDevice (Attempt 1)", "raw"),
        0xc0df9:  ("CreateDevice Attempt 1 FAILED", "raw"),
        0xc0e2b:  ("Call IDirect3D9::CreateDevice (Attempt 2)", "raw"),
        0xc0e30:  ("CreateDevice Attempt 2 FAILED", "raw"),
        0xc0e39:  ("CreateDevice SUCCESS!", "raw"),
    }

    de = DEBUG_EVENT()
    while True:
        if not kernel32.WaitForDebugEvent(ctypes.byref(de), 5000):
            print("[!] Timeout waiting for debug event")
            break

        continue_status = DBG_CONTINUE
        code = de.dwDebugEventCode

        if code == CREATE_PROCESS_DEBUG_EVENT:
            pass

        elif code == LOAD_DLL_DEBUG_EVENT:
            base = de.u.LoadDll.lpBaseOfDll
            buf = ctypes.create_unicode_buffer(512)
            ctypes.windll.kernel32.GetFinalPathNameByHandleW(de.u.LoadDll.hFile, buf, 512, 0)
            dll_name = os.path.basename(buf.value) if buf.value else ""
            if dll_name:
                print(f"  [DLL] Loaded: {dll_name} at 0x{base:08x}")
            if "GameClient.dll" in dll_name or not game_client_base:
                # Check pe export or section
                test_buf = (ctypes.c_byte * 2)()
                read = ctypes.c_size_t()
                kernel32.ReadProcessMemory(pi.hProcess, base, test_buf, 2, ctypes.byref(read))
                if bytes(test_buf) == b'MZ':
                    # Read DOS header e_lfanew
                    lfanew_buf = (ctypes.c_byte * 4)()
                    kernel32.ReadProcessMemory(pi.hProcess, base + 0x3c, lfanew_buf, 4, ctypes.byref(read))
                    lfanew = int.from_bytes(bytes(lfanew_buf), 'little')
                    # Read Export Directory RVA
                    exp_buf = (ctypes.c_byte * 8)()
                    kernel32.ReadProcessMemory(pi.hProcess, base + lfanew + 0x78, exp_buf, 8, ctypes.byref(read))
                    exp_rva = int.from_bytes(bytes(exp_buf)[:4], 'little')
                    if exp_rva:
                        exp_name_buf = (ctypes.c_byte * 30)()
                        kernel32.ReadProcessMemory(pi.hProcess, base + exp_rva + 0x0c, exp_name_buf, 4, ctypes.byref(read))
                        name_rva = int.from_bytes(bytes(exp_name_buf)[:4], 'little')
                        mod_name_raw = (ctypes.c_byte * 32)()
                        kernel32.ReadProcessMemory(pi.hProcess, base + name_rva, mod_name_raw, 32, ctypes.byref(read))
                        s_name = bytes(mod_name_raw).split(b'\x00')[0].decode(errors='ignore')
                        if s_name.lower() == "gameclient.dll":
                            game_client_base = base
                            print(f"[+] Loaded GameClient.dll at 0x{base:08x}")
                            # Set breakpoints!
                            for rva, (desc, target) in points_to_set.items():
                                bp_addr = (game_client_base if target == "gc" else the_raw_base) + rva
                                b_val = (ctypes.c_byte * 1)()
                                kernel32.ReadProcessMemory(pi.hProcess, bp_addr, b_val, 1, ctypes.byref(read))
                                orig_bytes[bp_addr] = bytes(b_val)[0]
                                int3 = (ctypes.c_byte * 1)(0xcc)
                                written = ctypes.c_size_t()
                                kernel32.WriteProcessMemory(pi.hProcess, bp_addr, int3, 1, ctypes.byref(written))
                                kernel32.FlushInstructionCache(pi.hProcess, bp_addr, 1)
                                breakpoints[bp_addr] = desc
                                print(f"    BP set at 0x{bp_addr:08x}: {desc}")

        elif code == EXCEPTION_DEBUG_EVENT:
            exc_code = de.u.Exception.ExceptionRecord.ExceptionCode
            exc_addr = de.u.Exception.ExceptionRecord.ExceptionAddress

            if exc_code in (0x80000003, 0x4000001F): # STATUS_BREAKPOINT or STATUS_WX86_BREAKPOINT
                if exc_addr in breakpoints:
                    desc = breakpoints[exc_addr]
                    print(f"[*] HIT BREAKPOINT: 0x{exc_addr:08x} -> {desc}")

                    # Restore original byte
                    orig = (ctypes.c_byte * 1)(orig_bytes[exc_addr])
                    written = ctypes.c_size_t()
                    kernel32.WriteProcessMemory(pi.hProcess, exc_addr, orig, 1, ctypes.byref(written))
                    kernel32.FlushInstructionCache(pi.hProcess, exc_addr, 1)

                    # Inspect registers
                    h_thread = kernel32.OpenThread(0x001F03FF, False, de.dwThreadId)
                    if h_thread:
                        class WOW64_CONTEXT(ctypes.Structure):
                            _fields_ = [
                                ('ContextFlags', wintypes.DWORD),
                                ('Dr0', wintypes.DWORD), ('Dr1', wintypes.DWORD), ('Dr2', wintypes.DWORD), ('Dr3', wintypes.DWORD), ('Dr6', wintypes.DWORD), ('Dr7', wintypes.DWORD),
                                ('FloatSave', ctypes.c_byte * 112),
                                ('SegGs', wintypes.DWORD), ('SegFs', wintypes.DWORD), ('SegEs', wintypes.DWORD), ('SegDs', wintypes.DWORD),
                                ('Edi', wintypes.DWORD), ('Esi', wintypes.DWORD), ('Ebx', wintypes.DWORD), ('Edx', wintypes.DWORD), ('Ecx', wintypes.DWORD), ('Eax', wintypes.DWORD),
                                ('Ebp', wintypes.DWORD), ('Eip', wintypes.DWORD), ('SegCs', wintypes.DWORD), ('EFlags', wintypes.DWORD), ('Esp', wintypes.DWORD), ('SegSs', wintypes.DWORD),
                                ('ExtendedRegisters', ctypes.c_byte * 512),
                            ]
                        ctx = WOW64_CONTEXT()
                        ctx.ContextFlags = 0x10007 # WOW64_CONTEXT_FULL
                        if kernel32.Wow64GetThreadContext(h_thread, ctypes.byref(ctx)):
                            print(f"    EIP=0x{ctx.Eip:08x}, EAX=0x{ctx.Eax:08x}, ECX=0x{ctx.Ecx:08x}, EDX=0x{ctx.Edx:08x}, ESP=0x{ctx.Esp:08x}")
                            if exc_addr == game_client_base + 0x23b1b7: # SetRenderMode
                                rmode_buf = (ctypes.c_byte * 32)()
                                read = ctypes.c_size_t()
                                kernel32.ReadProcessMemory(pi.hProcess, ctx.Edx, rmode_buf, 32, ctypes.byref(read))
                                vals = [int.from_bytes(bytes(rmode_buf)[i:i+4], 'little') for i in range(0, 32, 4)]
                                print(f"    RenderMode struct at 0x{ctx.Edx:08x}: {vals}")
                                fn_buf = (ctypes.c_byte * 4)()
                                kernel32.ReadProcessMemory(pi.hProcess, 0x85ff10, fn_buf, 4, ctypes.byref(read))
                                fn_val = int.from_bytes(bytes(fn_buf), 'little')
                                print(f"    [0x85ff10] = 0x{fn_val:08x}")
                            if exc_addr == the_raw_base + 0xc0deb: # CreateDevice
                                stack_buf = (ctypes.c_byte * 28)()
                                read = ctypes.c_size_t()
                                kernel32.ReadProcessMemory(pi.hProcess, ctx.Esp, stack_buf, 28, ctypes.byref(read))
                                args = [int.from_bytes(bytes(stack_buf)[i:i+4], 'little') for i in range(0, 28, 4)]
                                print(f"    CreateDevice args [this, adapter, devtype, hwnd, flags, &d3dpp, &pDev]: {[hex(x) for x in args]}")
                                # read d3dpp at args[5]
                                d3dpp_buf = (ctypes.c_byte * 56)()
                                kernel32.ReadProcessMemory(pi.hProcess, args[5], d3dpp_buf, 56, ctypes.byref(read))
                                d3dpp = [int.from_bytes(bytes(d3dpp_buf)[i:i+4], 'little') for i in range(0, 56, 4)]
                                print(f"    D3DPRESENT_PARAMETERS: Width={d3dpp[0]}, Height={d3dpp[1]}, Format={hex(d3dpp[2])}, Count={d3dpp[3]}, MSType={d3dpp[4]}, SwapEff={d3dpp[6]}, hWnd={hex(d3dpp[7])}, Windowed={d3dpp[8]}, AutoDS={d3dpp[9]}, DSFormat={hex(d3dpp[10])}, Flags={hex(d3dpp[11])}, Hz={d3dpp[12]}, Interval={hex(d3dpp[13])}")
                            if exc_addr in (the_raw_base + 0xc0df9, the_raw_base + 0xc0e30):
                                print(f"    CreateDevice FAILED with HRESULT: 0x{ctx.Eax:08x}")
                            ctx.Eip = exc_addr
                            kernel32.Wow64SetThreadContext(h_thread, ctypes.byref(ctx))
                        kernel32.CloseHandle(h_thread)

            elif exc_code in (0x80000004, 0x40000020): # STATUS_SINGLE_STEP or STATUS_WX86_SINGLE_STEP
                pass
            else:
                h_thread = kernel32.OpenThread(0x001F03FF, False, de.dwThreadId)
                ret_addr = 0
                if h_thread:
                    class WOW64_CONTEXT(ctypes.Structure):
                        _fields_ = [
                            ('ContextFlags', wintypes.DWORD),
                            ('Dr0', wintypes.DWORD), ('Dr1', wintypes.DWORD), ('Dr2', wintypes.DWORD), ('Dr3', wintypes.DWORD), ('Dr6', wintypes.DWORD), ('Dr7', wintypes.DWORD),
                            ('FloatSave', ctypes.c_byte * 112),
                            ('SegGs', wintypes.DWORD), ('SegFs', wintypes.DWORD), ('SegEs', wintypes.DWORD), ('SegDs', wintypes.DWORD),
                            ('Edi', wintypes.DWORD), ('Esi', wintypes.DWORD), ('Ebx', wintypes.DWORD), ('Edx', wintypes.DWORD), ('Ecx', wintypes.DWORD), ('Eax', wintypes.DWORD),
                            ('Ebp', wintypes.DWORD), ('Eip', wintypes.DWORD), ('SegCs', wintypes.DWORD), ('EFlags', wintypes.DWORD), ('Esp', wintypes.DWORD), ('SegSs', wintypes.DWORD),
                            ('ExtendedRegisters', ctypes.c_byte * 512),
                        ]
                    ctx = WOW64_CONTEXT()
                    ctx.ContextFlags = 0x10007 # WOW64_CONTEXT_FULL
                    if kernel32.Wow64GetThreadContext(h_thread, ctypes.byref(ctx)):
                        # Read stack frames (64 bytes = 16 dwords)
                        ret_buf = (ctypes.c_byte * 64)()
                        read = ctypes.c_size_t()
                        kernel32.ReadProcessMemory(pi.hProcess, ctx.Esp, ret_buf, 64, ctypes.byref(read))
                        ret_addrs = [hex(int.from_bytes(bytes(ret_buf)[i:i+4], 'little')) for i in range(0, 64, 4)]
                        print(f"[!] Other exception: 0x{exc_code:08x} at 0x{exc_addr:08x}, Thread EIP=0x{ctx.Eip:08x}, Stack={ret_addrs}")
                    kernel32.CloseHandle(h_thread)
                continue_status = DBG_EXCEPTION_NOT_HANDLED

        elif code == EXIT_PROCESS_DEBUG_EVENT:
            exit_code = de.u.raw[0]
            print(f"[+] Process exited with code: {exit_code}")
            kernel32.ContinueDebugEvent(de.dwProcessId, de.dwThreadId, continue_status)
            break

        kernel32.ContinueDebugEvent(de.dwProcessId, de.dwThreadId, continue_status)

if __name__ == "__main__":
    main()
