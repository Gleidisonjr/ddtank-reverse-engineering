import ctypes
from ctypes import wintypes
import os
import sys

kernel32 = ctypes.windll.kernel32
kernel32.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]

DEBUG_PROCESS = 0x00000001
DBG_CONTINUE = 0x00010002
DBG_EXCEPTION_NOT_HANDLED = 0x80010001

CREATE_PROCESS_DEBUG_EVENT = 3
EXIT_PROCESS_DEBUG_EVENT = 5
LOAD_DLL_DEBUG_EVENT = 6
EXCEPTION_DEBUG_EVENT = 1

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

class CREATE_PROCESS_DEBUG_INFO(ctypes.Structure):
    _fields_ = [
        ('hFile', wintypes.HANDLE),
        ('hProcess', wintypes.HANDLE),
        ('hThread', wintypes.HANDLE),
        ('lpBaseOfImage', ctypes.c_void_p),
        ('dwDebugInfoFileOffset', wintypes.DWORD),
        ('nDebugInfoSize', wintypes.DWORD),
        ('lpThreadLocalBase', ctypes.c_void_p),
        ('lpStartAddress', ctypes.c_void_p),
        ('lpImageName', ctypes.c_void_p),
        ('fUnicode', wintypes.WORD),
    ]

class DEBUG_EVENT_UNION(ctypes.Union):
    _fields_ = [
        ('Exception', EXCEPTION_DEBUG_INFO),
        ('CreateProcessInfo', CREATE_PROCESS_DEBUG_INFO),
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

def set_hw_breakpoints(h_thread):
    ctx = WOW64_CONTEXT()
    ctx.ContextFlags = 0x10010 # WOW64_CONTEXT_DEBUG_REGISTERS
    kernel32.Wow64GetThreadContext(h_thread, ctypes.byref(ctx))
    ctx.Dr0 = 0x004be247 # RenderInit (0x4be247)
    ctx.Dr1 = 0x004c0deb # IDirect3D9::CreateDevice call
    ctx.Dr2 = 0x004c0dee # Right after CreateDevice call
    ctx.Dr3 = 0x0040f2e7 # SetRenderMode return path
    # Dr7:
    # bit 0: Dr0 local enable
    # bit 2: Dr1 local enable
    # bit 4: Dr2 local enable
    # bit 6: Dr3 local enable
    # bits 16-17: Dr0 condition (00 = execute)
    # bits 20-21: Dr1 condition (00 = execute)
    # bits 24-25: Dr2 condition (00 = execute)
    # bits 28-29: Dr3 condition (00 = execute)
    ctx.Dr7 = 0x00000055 # enable Dr0, Dr1, Dr2, Dr3 for execution
    kernel32.Wow64SetThreadContext(h_thread, ctypes.byref(ctx))

def main():
    sys.stdout.reconfigure(line_buffering=True)
    si = STARTUPINFO()
    si.cb = ctypes.sizeof(si)
    pi = PROCESS_INFORMATION()

    os.environ["__COMPAT_LAYER"] = "RunAsInvoker"
    client_dir = r"C:\Users\dopamine\Desktop\Projetos\Reverse Engineering\targets\district-187\client-rebirth"
    exe = os.path.join(client_dir, "TheRaw.exe")
    cmd = f'"{exe}" -arch game -windowtitle "District 187: Sin Streets" +gs_ip 127.0.0.1 +gs_port 12000 +windowed 1 +ScreenWidth 1920 +ScreenHeight 1080'

    os.system("taskkill /f /im TheRaw.exe >nul 2>&1")

    res = kernel32.CreateProcessW(
        None, cmd, None, None, False, DEBUG_PROCESS, None, client_dir, ctypes.byref(si), ctypes.byref(pi)
    )
    if not res:
        print("CreateProcess failed:", kernel32.GetLastError())
        return

    print(f"[+] Started TheRaw.exe PID {pi.dwProcessId}")
    de = DEBUG_EVENT()

    while True:
        if not kernel32.WaitForDebugEvent(ctypes.byref(de), 5000):
            print("[!] Timeout")
            break

        code = de.dwDebugEventCode
        continue_status = DBG_CONTINUE

        if code == CREATE_PROCESS_DEBUG_EVENT:
            pass

        elif code == LOAD_DLL_DEBUG_EVENT:
            buf = ctypes.create_unicode_buffer(512)
            ctypes.windll.kernel32.GetFinalPathNameByHandleW(de.u.LoadDll.hFile, buf, 512, 0)
            dll_name = os.path.basename(buf.value) if buf.value else ""
            if "gameclient.dll" in dll_name.lower():
                h_thread = kernel32.OpenThread(0x001F03FF, False, de.dwThreadId)
                if h_thread:
                    set_hw_breakpoints(h_thread)
                    kernel32.CloseHandle(h_thread)
                    print(f"[+] Enabled Hardware Breakpoints on Thread {de.dwThreadId} after GameClient.dll load")

        elif code == EXCEPTION_DEBUG_EVENT:
            exc_code = de.u.Exception.ExceptionRecord.ExceptionCode
            exc_addr = de.u.Exception.ExceptionRecord.ExceptionAddress

            if exc_code in (0x80000004, 0x40000020): # STATUS_SINGLE_STEP / STATUS_WX86_SINGLE_STEP
                h_thread = kernel32.OpenThread(0x001F03FF, False, de.dwThreadId)
                if h_thread:
                    ctx = WOW64_CONTEXT()
                    ctx.ContextFlags = 0x10017 # WOW64_CONTEXT_FULL | DEBUG_REGISTERS
                    kernel32.Wow64GetThreadContext(h_thread, ctypes.byref(ctx))
                    eip = ctx.Eip

                    if eip == 0x004be247:
                        # RenderInit
                        print(f"[*] HW BP: Entered 0x4be247 (RenderInit)")
                        # Read [0x8504f4]
                        val_buf = (ctypes.c_byte * 4)()
                        read = ctypes.c_size_t()
                        kernel32.ReadProcessMemory(pi.hProcess, 0x8504f4, val_buf, 4, ctypes.byref(read))
                        val = int.from_bytes(bytes(val_buf), 'little')
                        print(f"    windowed cvar [0x8504f4] = 0x{val:08x}")

                    elif eip == 0x004c0deb:
                        # CreateDevice call
                        print(f"[*] HW BP: Reached 0x4c0deb (IDirect3D9::CreateDevice call)")
                        stack_buf = (ctypes.c_byte * 28)()
                        read = ctypes.c_size_t()
                        kernel32.ReadProcessMemory(pi.hProcess, ctx.Esp, stack_buf, 28, ctypes.byref(read))
                        args = [int.from_bytes(bytes(stack_buf)[i:i+4], 'little') for i in range(0, 28, 4)]
                        print(f"    CreateDevice args [this, adapter, devtype, hwnd, flags, &d3dpp, &pDev]: {[hex(x) for x in args]}")
                        d3dpp_buf = (ctypes.c_byte * 56)()
                        kernel32.ReadProcessMemory(pi.hProcess, args[5], d3dpp_buf, 56, ctypes.byref(read))
                        d3dpp = [int.from_bytes(bytes(d3dpp_buf)[i:i+4], 'little') for i in range(0, 56, 4)]
                        print(f"    d3dpp: W={d3dpp[0]}, H={d3dpp[1]}, Fmt={hex(d3dpp[2])}, Cnt={d3dpp[3]}, MS={d3dpp[4]}, Swap={d3dpp[6]}, hWnd={hex(d3dpp[7])}, Win={d3dpp[8]}, DS={d3dpp[9]}, DSFmt={hex(d3dpp[10])}, Flags={hex(d3dpp[11])}, Hz={d3dpp[12]}, Int={hex(d3dpp[13])}")

                    elif eip == 0x004c0dee:
                        # Right after CreateDevice call
                        print(f"[*] HW BP: Returned from CreateDevice -> EAX (HRESULT) = 0x{ctx.Eax:08x}")

                    elif eip == 0x0040f2e7:
                        print(f"[*] HW BP: Reached SetRenderMode return path -> EAX = 0x{ctx.Eax:08x}")

                    # Reset Dr6 and ensure Dr7 remains active
                    ctx.Dr6 = 0
                    ctx.Dr7 = 0x00000055
                    kernel32.Wow64SetThreadContext(h_thread, ctypes.byref(ctx))
                    kernel32.CloseHandle(h_thread)

            elif exc_code in (0x80000003, 0x4000001F):
                pass
            else:
                continue_status = DBG_EXCEPTION_NOT_HANDLED

        elif code == EXIT_PROCESS_DEBUG_EVENT:
            print("[+] Process exited")
            break

        kernel32.ContinueDebugEvent(de.dwProcessId, de.dwThreadId, continue_status)

if __name__ == "__main__":
    main()
