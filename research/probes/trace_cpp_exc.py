import ctypes
from ctypes import wintypes
import os
import sys

kernel32 = ctypes.windll.kernel32
kernel32.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]

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

        elif code == 1: # EXCEPTION
            exc_code = de.u.Exception.ExceptionRecord.ExceptionCode
            exc_addr = de.u.Exception.ExceptionRecord.ExceptionAddress

            if exc_code == 0xe06d7363:
                h_thread = kernel32.OpenThread(0x001F03FF, False, de.dwThreadId)
                if h_thread:
                    ctx = WOW64_CONTEXT()
                    ctx.ContextFlags = 0x10007 # WOW64_CONTEXT_CONTROL | INTEGER
                    kernel32.Wow64GetThreadContext(h_thread, ctypes.byref(ctx))
                    print(f"[!] C++ EXCEPTION 0xe06d7363 at EIP=0x{ctx.Eip:08x}, ESP=0x{ctx.Esp:08x}, EBP=0x{ctx.Ebp:08x}")
                    # Read stack trace
                    stack_buf = (ctypes.c_byte * 128)()
                    read = ctypes.c_size_t()
                    kernel32.ReadProcessMemory(pi.hProcess, ctx.Esp, stack_buf, 128, ctypes.byref(read))
                    stack = [int.from_bytes(bytes(stack_buf)[i:i+4], 'little') for i in range(0, 128, 4)]
                    print(f"    Stack top 16 dwords: {[hex(x) for x in stack[:16]]}")
                    # Match stack addrs against modules
                    for addr in stack:
                        if 0x400000 <= addr <= 0x860000:
                            print(f"      -> TheRaw.exe + 0x{addr - 0x400000:06x} (0x{addr:08x})")
                        for base, name in modules.items():
                            if base <= addr <= base + 0x1000000:
                                print(f"      -> {name} + 0x{addr - base:06x} (0x{addr:08x})")
                    kernel32.CloseHandle(h_thread)

            if exc_code not in (0x80000003, 0x4000001F):
                continue_status = DBG_EXCEPTION_NOT_HANDLED

        elif code == 5: # EXIT_PROCESS
            print(f"[+] Process exited")
            break

        kernel32.ContinueDebugEvent(de.dwProcessId, de.dwThreadId, continue_status)

if __name__ == "__main__":
    main()
