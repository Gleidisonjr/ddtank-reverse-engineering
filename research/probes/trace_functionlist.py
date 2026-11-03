import os
import subprocess
import time
import ctypes
from ctypes import wintypes
import sys

kernel32 = ctypes.windll.kernel32
user32 = ctypes.windll.user32

DEBUG_PROCESS = 0x00000001
CREATE_SUSPENDED = 0x00000004
DBG_CONTINUE = 0x00010002
DBG_EXCEPTION_NOT_HANDLED = 0x80010001
EXCEPTION_DEBUG_EVENT = 1
CREATE_PROCESS_DEBUG_EVENT = 3
EXIT_PROCESS_DEBUG_EVENT = 5
LOAD_DLL_DEBUG_EVENT = 6

class DEBUG_EVENT(ctypes.Structure):
    class u(ctypes.Union):
        class EXCEPTION_DEBUG_INFO(ctypes.Structure):
            class EXCEPTION_RECORD(ctypes.Structure):
                pass
            EXCEPTION_RECORD._fields_ = [
                ('ExceptionCode', wintypes.DWORD),
                ('ExceptionFlags', wintypes.DWORD),
                ('ExceptionRecord', ctypes.c_void_p),
                ('ExceptionAddress', ctypes.c_void_p),
                ('NumberParameters', wintypes.DWORD),
                ('ExceptionInformation', wintypes.WPARAM * 15),
            ]
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
        _fields_ = [
            ('Exception', EXCEPTION_DEBUG_INFO),
            ('LoadDll', LOAD_DLL_DEBUG_INFO),
            ('pad', ctypes.c_byte * 160),
        ]
    _fields_ = [
        ('dwDebugEventCode', wintypes.DWORD),
        ('dwProcessId', wintypes.DWORD),
        ('dwThreadId', wintypes.DWORD),
        ('u', u),
    ]

kernel32.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
kernel32.ReadProcessMemory.restype = wintypes.BOOL
kernel32.WriteProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
kernel32.WriteProcessMemory.restype = wintypes.BOOL

os.environ['__COMPAT_LAYER'] = 'RunAsInvoker'
client_dir = os.path.abspath(r'targets\district-187\client-rebirth')
raw_exe = os.path.join(client_dir, 'TheRaw.exe')

subprocess.run(['taskkill', '/F', '/IM', 'TheRaw.exe'], capture_output=True)
time.sleep(0.3)

class STARTUPINFOA(ctypes.Structure):
    _fields_ = [
        ('cb', wintypes.DWORD),
        ('lpReserved', wintypes.LPSTR),
        ('lpDesktop', wintypes.LPSTR),
        ('lpTitle', wintypes.LPSTR),
        ('dwX', wintypes.DWORD), ('dwY', wintypes.DWORD),
        ('dwXSize', wintypes.DWORD), ('dwYSize', wintypes.DWORD),
        ('dwXCountChars', wintypes.DWORD), ('dwYCountChars', wintypes.DWORD),
        ('dwFillAttribute', wintypes.DWORD),
        ('dwFlags', wintypes.DWORD),
        ('wShowWindow', wintypes.WORD),
        ('cbReserved2', wintypes.WORD),
        ('lpReserved2', ctypes.c_void_p),
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

si = STARTUPINFOA()
si.cb = ctypes.sizeof(si)
pi = PROCESS_INFORMATION()

cmdline = f'"{raw_exe}" -arch game -windowtitle "District 187: Sin Streets" +gs_ip 127.0.0.1 +gs_port 12000 +windowed 1 +ScreenWidth 1920 +ScreenHeight 1080'

res = kernel32.CreateProcessA(
    None, cmdline.encode('latin1'),
    None, None, False,
    DEBUG_PROCESS,
    None, client_dir.encode('latin1'),
    ctypes.byref(si), ctypes.byref(pi)
)

if not res:
    print("CreateProcess failed:", kernel32.GetLastError(), flush=True)
    sys.exit(1)

print("Started TheRaw under debugger, PID:", pi.dwProcessId, flush=True)

game_client_base = 0
bp_error = 0
orig_byte = None
de = DEBUG_EVENT()

while True:
    if not kernel32.WaitForDebugEvent(ctypes.byref(de), 1000):
        exit_code = wintypes.DWORD()
        kernel32.GetExitCodeProcess(pi.hProcess, ctypes.byref(exit_code))
        if exit_code.value != 259: # STILL_ACTIVE
            print("Process terminated with code:", exit_code.value, flush=True)
            break
        continue

    continue_status = DBG_CONTINUE
    code = de.dwDebugEventCode

    if code == LOAD_DLL_DEBUG_EVENT:
        raw_base = de.u.LoadDll.lpBaseOfDll
        if raw_base:
            base = ctypes.c_void_p(raw_base).value
            if base:
                test_buf = (ctypes.c_byte * 12)()
                read = ctypes.c_size_t()
                kernel32.ReadProcessMemory(pi.hProcess, ctypes.c_void_p(base + 0x480f50 - 0x10000000), test_buf, 12, ctypes.byref(read))
                if bytes(test_buf).startswith(b'FunctionList'):
                    game_client_base = base
                    print(f"[+] Found GameClient.dll at 0x{base:08x}", flush=True)
                    bp_error = base + (0x10005e10 - 0x10000000)
                    b_val = (ctypes.c_byte * 1)()
                    kernel32.ReadProcessMemory(pi.hProcess, ctypes.c_void_p(bp_error), b_val, 1, ctypes.byref(read))
                    orig_byte = bytes(b_val)[0]
                    int3 = (ctypes.c_byte * 1)(0xCC)
                    kernel32.WriteProcessMemory(pi.hProcess, ctypes.c_void_p(bp_error), int3, 1, ctypes.byref(read))
                    print(f"[+] Set breakpoint at Error popup: 0x{bp_error:08x}", flush=True)

    elif code == EXCEPTION_DEBUG_EVENT:
        exc = de.u.Exception.ExceptionRecord
        exc_code = exc.ExceptionCode
        exc_addr = ctypes.c_void_p(exc.ExceptionAddress).value
        if exc_code == 0x80000003: # STATUS_BREAKPOINT
            if game_client_base and exc_addr == bp_error:
                print(f"\n[!!!] HIT BREAKPOINT AT 0x{exc_addr:08x} (FunctionList Error Popup)!", flush=True)
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
                    ctx.ContextFlags = 0x10007
                    kernel32.Wow64GetThreadContext(h_thread, ctypes.byref(ctx))
                    print(f"Registers: EAX=0x{ctx.Eax:08x}, ECX=0x{ctx.Ecx:08x}, EDX=0x{ctx.Edx:08x}, EBX=0x{ctx.Ebx:08x}, ESP=0x{ctx.Esp:08x}, EBP=0x{ctx.Ebp:08x}, ESI=0x{ctx.Esi:08x}, EDI=0x{ctx.Edi:08x}", flush=True)
                    
                    str_buf = (ctypes.c_byte * 32)()
                    read = ctypes.c_size_t()
                    kernel32.ReadProcessMemory(pi.hProcess, ctypes.c_void_p(ctx.Esp + 0xc), str_buf, 32, ctypes.byref(read))
                    s_bytes = bytes(str_buf)
                    s_len = int.from_bytes(s_bytes[16:20], 'little')
                    s_cap = int.from_bytes(s_bytes[20:24], 'little')
                    print(f"String header: len={s_len}, cap={s_cap}", flush=True)
                    if s_cap >= 16:
                        ptr = int.from_bytes(s_bytes[0:4], 'little')
                        val_buf = (ctypes.c_byte * (s_len + 1))()
                        kernel32.ReadProcessMemory(pi.hProcess, ctypes.c_void_p(ptr), val_buf, s_len, ctypes.byref(read))
                        actual_str = bytes(val_buf)[:s_len]
                    else:
                        actual_str = s_bytes[:s_len]
                    print(f"--> Offending FunctionName: '{actual_str.decode('latin1', errors='ignore')}' (hex: {actual_str.hex()})", flush=True)

                    stack_buf = (ctypes.c_byte * 64)()
                    kernel32.ReadProcessMemory(pi.hProcess, ctypes.c_void_p(ctx.Esp), stack_buf, 64, ctypes.byref(read))
                    words = [int.from_bytes(bytes(stack_buf)[i:i+4], 'little') for i in range(0, 64, 4)]
                    print(f"Stack words: {[hex(w) for w in words[:10]]}", flush=True)
                    kernel32.CloseHandle(h_thread)
                break

    elif code == EXIT_PROCESS_DEBUG_EVENT:
        print("Process exited", flush=True)
        break

    kernel32.ContinueDebugEvent(de.dwProcessId, de.dwThreadId, continue_status)

kernel32.TerminateProcess(pi.hProcess, 0)
kernel32.CloseHandle(pi.hThread)
kernel32.CloseHandle(pi.hProcess)
