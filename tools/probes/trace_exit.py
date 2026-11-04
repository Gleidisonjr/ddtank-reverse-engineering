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

class WOW64_CONTEXT(ctypes.Structure):
    _fields_ = [
        ('ContextFlags', wintypes.DWORD),
        ('Dr0', wintypes.DWORD),
        ('Dr1', wintypes.DWORD),
        ('Dr2', wintypes.DWORD),
        ('Dr3', wintypes.DWORD),
        ('Dr6', wintypes.DWORD),
        ('Dr7', wintypes.DWORD),
        ('FloatSave', ctypes.c_byte * 112),
        ('SegGs', wintypes.DWORD),
        ('SegFs', wintypes.DWORD),
        ('SegEs', wintypes.DWORD),
        ('SegDs', wintypes.DWORD),
        ('Edi', wintypes.DWORD),
        ('Esi', wintypes.DWORD),
        ('Ebx', wintypes.DWORD),
        ('Edx', wintypes.DWORD),
        ('Ecx', wintypes.DWORD),
        ('Eax', wintypes.DWORD),
        ('Ebp', wintypes.DWORD),
        ('Eip', wintypes.DWORD),
        ('SegCs', wintypes.DWORD),
        ('EFlags', wintypes.DWORD),
        ('Esp', wintypes.DWORD),
        ('SegSs', wintypes.DWORD),
        ('ExtendedRegisters', ctypes.c_byte * 512),
    ]

def main():
    si = STARTUPINFO()
    si.cb = ctypes.sizeof(si)
    pi = PROCESS_INFORMATION()

    os.environ["__COMPAT_LAYER"] = "RunAsInvoker"
    client_dir = r"C:\Users\dopamine\Desktop\Projetos\Reverse Engineering\targets\district-187\client-rebirth"
    exe = os.path.join(client_dir, "TheRaw.exe")
    cmd = f'"{exe}" -arch game -windowtitle "District 187: Sin Streets" +gs_ip 127.0.0.1 +gs_port 12000 +windowed 1 +ScreenWidth 1920 +ScreenHeight 1080 +ShowLog 1'

    os.system("taskkill /f /im TheRaw.exe >nul 2>&1")

    res = kernel32.CreateProcessW(None, cmd, None, None, False, DEBUG_PROCESS, None, client_dir, ctypes.byref(si), ctypes.byref(pi))
    if not res:
        print("CreateProcess failed:", kernel32.GetLastError())
        return

    print(f"[+] Started TheRaw.exe PID {pi.dwProcessId}")
    modules = {}
    kernel32_base = None
    exit_process_addr = None
    orig_byte = None

    de = DEBUG_EVENT()
    while True:
        if not kernel32.WaitForDebugEvent(ctypes.byref(de), 5000):
            print("[!] Timeout")
            break

        code = de.dwDebugEventCode
        continue_status = DBG_CONTINUE

        if code == 6: # LOAD_DLL
            base = de.u.LoadDll.lpBaseOfDll
            buf = ctypes.create_unicode_buffer(512)
            ctypes.windll.kernel32.GetFinalPathNameByHandleW(de.u.LoadDll.hFile, buf, 512, 0)
            dll_name = os.path.basename(buf.value) if buf.value else f"0x{base:08x}"
            modules[base] = dll_name
            if "gameclient" in dll_name.lower():
                print(f"[+] LOADED: {dll_name} at 0x{base:08x}")
            if "kernel32.dll" == dll_name.lower() and not kernel32_base:
                kernel32_base = base
                # Find ExitProcess export in 32-bit kernel32
                # In WOW64, kernel32 in the target process is 32-bit.
                # Let's read export dir
                import pefile
                try:
                    k32_pe = pefile.PE(buf.value)
                    for exp in k32_pe.DIRECTORY_ENTRY_EXPORT.symbols:
                        if exp.name == b'ExitProcess':
                            exit_process_addr = base + exp.address
                            # Write 0xCC
                            b = (ctypes.c_byte * 1)()
                            read = ctypes.c_size_t()
                            kernel32.ReadProcessMemory(pi.hProcess, exit_process_addr, b, 1, ctypes.byref(read))
                            orig_byte = bytes(b)[0]
                            cc = (ctypes.c_byte * 1)(0xcc)
                            written = ctypes.c_size_t()
                            kernel32.WriteProcessMemory(pi.hProcess, exit_process_addr, cc, 1, ctypes.byref(written))
                            kernel32.FlushInstructionCache(pi.hProcess, exit_process_addr, 1)
                            print(f"[+] Hooked ExitProcess at 0x{exit_process_addr:08x}")
                            break
                except Exception as e:
                    print(f"[!] Hook error: {e}")

        elif code == 1: # EXCEPTION
            exc_code = de.u.Exception.ExceptionRecord.ExceptionCode
            exc_addr = de.u.Exception.ExceptionRecord.ExceptionAddress

            if exc_code in (0x80000003, 0x4000001F) and exc_addr == exit_process_addr:
                h_thread = kernel32.OpenThread(0x001F03FF, False, de.dwThreadId)
                if h_thread:
                    ctx = WOW64_CONTEXT()
                    ctx.ContextFlags = 0x10007 # WOW64_CONTEXT_CONTROL | INTEGER
                    kernel32.Wow64GetThreadContext(h_thread, ctypes.byref(ctx))
                    # Read return address and exit code from stack
                    stack_buf = (ctypes.c_byte * 64)()
                    read = ctypes.c_size_t()
                    kernel32.ReadProcessMemory(pi.hProcess, ctx.Esp, stack_buf, 64, ctypes.byref(read))
                    stack = [int.from_bytes(bytes(stack_buf)[i:i+4], 'little') for i in range(0, 64, 4)]
                    ret_addr = stack[0]
                    exit_code = stack[1]
                    print(f"\n[***] ExitProcess CALLED! ExitCode={exit_code}, ReturnAddr=0x{ret_addr:08x}")
                    print(f"      Callstack:")
                    for addr in stack[:12]:
                        desc = f"0x{addr:08x}"
                        if 0x400000 <= addr <= 0x860000:
                            desc += f" (TheRaw.exe + 0x{addr - 0x400000:x})"
                        elif 0x10000000 <= addr <= 0x11000000:
                            desc += f" (GameClient.dll + 0x{addr - 0x10000000:x})"
                        for m_base, m_name in modules.items():
                            if m_base <= addr <= m_base + 0x1000000:
                                desc += f" ({m_name} + 0x{addr - m_base:x})"
                                break
                        print(f"        {desc}")
                    # Restore orig byte
                    old_b = (ctypes.c_byte * 1)(orig_byte)
                    written = ctypes.c_size_t()
                    kernel32.WriteProcessMemory(pi.hProcess, exit_process_addr, old_b, 1, ctypes.byref(written))
                    kernel32.FlushInstructionCache(pi.hProcess, exit_process_addr, 1)
                    ctx.Eip = exit_process_addr
                    kernel32.Wow64SetThreadContext(h_thread, ctypes.byref(ctx))
                    kernel32.CloseHandle(h_thread)

            elif exc_code not in (0x80000003, 0x4000001F):
                continue_status = DBG_EXCEPTION_NOT_HANDLED

        elif code == 5: # EXIT_PROCESS
            print(f"[+] Process exited")
            break

        kernel32.ContinueDebugEvent(de.dwProcessId, de.dwThreadId, continue_status)

if __name__ == "__main__":
    main()
