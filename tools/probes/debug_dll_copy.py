import ctypes, os, sys
from ctypes import wintypes

kernel32 = ctypes.windll.kernel32
DEBUG_PROCESS = 0x00000001
DBG_CONTINUE = 0x00010002
DBG_EXCEPTION_NOT_HANDLED = 0x80010001
EXCEPTION_DEBUG_EVENT = 1
LOAD_DLL_DEBUG_EVENT = 6
CREATE_PROCESS_DEBUG_EVENT = 3
EXIT_PROCESS_DEBUG_EVENT = 5

class STARTUPINFO(ctypes.Structure):
    _fields_ = [('cb', wintypes.DWORD), ('lpReserved', wintypes.LPWSTR), ('lpDesktop', wintypes.LPWSTR),
                ('lpTitle', wintypes.LPWSTR), ('dwX', wintypes.DWORD), ('dwY', wintypes.DWORD),
                ('dwXSize', wintypes.DWORD), ('dwYSize', wintypes.DWORD), ('dwXCountChars', wintypes.DWORD),
                ('dwYCountChars', wintypes.DWORD), ('dwFillAttribute', wintypes.DWORD), ('dwFlags', wintypes.DWORD),
                ('wShowWindow', wintypes.WORD), ('cbReserved2', wintypes.WORD), ('lpReserved2', ctypes.c_char_p),
                ('hStdInput', wintypes.HANDLE), ('hStdOutput', wintypes.HANDLE), ('hStdError', wintypes.HANDLE)]

class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [('hProcess', wintypes.HANDLE), ('hThread', wintypes.HANDLE),
                ('dwProcessId', wintypes.DWORD), ('dwThreadId', wintypes.DWORD)]

class EXCEPTION_RECORD(ctypes.Structure):
    pass
EXCEPTION_RECORD._fields_ = [('ExceptionCode', wintypes.DWORD), ('ExceptionFlags', wintypes.DWORD),
                            ('pExceptionRecord', ctypes.POINTER(EXCEPTION_RECORD)),
                            ('ExceptionAddress', ctypes.c_void_p), ('NumberParameters', wintypes.DWORD),
                            ('ExceptionInformation', ctypes.c_ulong * 15)]

class EXCEPTION_DEBUG_INFO(ctypes.Structure):
    _fields_ = [('ExceptionRecord', EXCEPTION_RECORD), ('dwFirstChance', wintypes.DWORD)]

class LOAD_DLL_DEBUG_INFO(ctypes.Structure):
    _fields_ = [('hFile', wintypes.HANDLE), ('lpBaseOfDll', ctypes.c_void_p),
                ('dwDebugInfoFileOffset', wintypes.DWORD), ('nDebugInfoSize', wintypes.DWORD),
                ('lpImageName', ctypes.c_void_p), ('fUnicode', wintypes.WORD)]

class DEBUG_EVENT_UNION(ctypes.Union):
    _fields_ = [('Exception', EXCEPTION_DEBUG_INFO), ('LoadDll', LOAD_DLL_DEBUG_INFO), ('raw', ctypes.c_byte * 160)]

class DEBUG_EVENT(ctypes.Structure):
    _fields_ = [('dwDebugEventCode', wintypes.DWORD), ('dwProcessId', wintypes.DWORD),
                ('dwThreadId', wintypes.DWORD), ('u', DEBUG_EVENT_UNION)]

class CONTEXT(ctypes.Structure):
    _fields_ = [('ContextFlags', wintypes.DWORD),
                ('Dr0', wintypes.DWORD), ('Dr1', wintypes.DWORD), ('Dr2', wintypes.DWORD), ('Dr3', wintypes.DWORD),
                ('Dr6', wintypes.DWORD), ('Dr7', wintypes.DWORD),
                ('FloatSave', ctypes.c_byte * 112),
                ('SegGs', wintypes.DWORD), ('SegFs', wintypes.DWORD), ('SegEs', wintypes.DWORD), ('SegDs', wintypes.DWORD),
                ('Edi', wintypes.DWORD), ('Esi', wintypes.DWORD), ('Ebx', wintypes.DWORD), ('Edx', wintypes.DWORD),
                ('Ecx', wintypes.DWORD), ('Eax', wintypes.DWORD), ('Ebp', wintypes.DWORD), ('Eip', wintypes.DWORD),
                ('SegCs', wintypes.DWORD), ('EFlags', wintypes.DWORD), ('Esp', wintypes.DWORD), ('SegSs', wintypes.DWORD),
                ('ExtendedRegisters', ctypes.c_byte * 512)]

CONTEXT_FULL = 0x00010007

def main():
    os.environ['__COMPAT_LAYER'] = 'RunAsInvoker'
    client_dir = r"C:\Users\dopamine\Desktop\Projetos\Reverse Engineering\targets\district-187\client-rebirth"
    exe = os.path.join(client_dir, 'TheRaw.exe')
    cmd = f'"{exe}" -archcfg Default.archcfg'

    os.system('taskkill /f /im TheRaw.exe >nul 2>&1')

    si = STARTUPINFO()
    si.cb = ctypes.sizeof(si)
    pi = PROCESS_INFORMATION()

    res = kernel32.CreateProcessW(None, cmd, None, None, False, DEBUG_PROCESS, None, client_dir, ctypes.byref(si), ctypes.byref(pi))
    if not res:
        print("CreateProcess failed:", kernel32.GetLastError())
        return

    bps = {
        0x492fc0: 'Before call 0x423019',
        0x492fe5: 'FAIL branch: GetLastError()',
        0x49304a: 'SUCCESS branch: LoadLibrary',
        0x423019: 'Inside 0x423019 entry',
        0x42308c: '0x423019 return FALSE (0)',
        0x4230c4: '0x423019 return TRUE (1)',
        0x403f13: 'Inside 0x403f13 (copy file attempt)',
        0x403fa4: '0x403f13 after 0x5a9277',
        0x403fc6: '0x403f13 FAIL',
        0x403fd4: '0x403f13 SUCCESS copy',
    }
    orig_bytes = {}
    read = ctypes.c_size_t()
    written = ctypes.c_size_t()

    for addr in bps:
        b = (ctypes.c_byte * 1)()
        kernel32.ReadProcessMemory(pi.hProcess, addr, b, 1, ctypes.byref(read))
        orig_bytes[addr] = bytes(b)[0]
        int3 = (ctypes.c_byte * 1)(0xcc)
        kernel32.WriteProcessMemory(pi.hProcess, addr, int3, 1, ctypes.byref(written))
        kernel32.FlushInstructionCache(pi.hProcess, addr, 1)

    de = DEBUG_EVENT()
    while True:
        if not kernel32.WaitForDebugEvent(ctypes.byref(de), 5000):
            print('Timeout')
            break
        status = DBG_CONTINUE
        code = de.dwDebugEventCode
        if code == EXIT_PROCESS_DEBUG_EVENT:
            print('Process exited')
            break
        elif code == EXCEPTION_DEBUG_EVENT:
            exc_code = de.u.Exception.ExceptionRecord.ExceptionCode
            exc_addr = de.u.Exception.ExceptionRecord.ExceptionAddress
            if exc_code == 0x80000003 and exc_addr in bps:
                desc = bps[exc_addr]
                hThread = kernel32.OpenThread(0x001F03FF, False, de.dwThreadId)
                ctx = CONTEXT()
                ctx.ContextFlags = CONTEXT_FULL
                kernel32.GetThreadContext(hThread, ctypes.byref(ctx))
                print(f'[BP] 0x{exc_addr:08x}: {desc} | EAX=0x{ctx.Eax:08x} EBX=0x{ctx.Ebx:08x} ECX=0x{ctx.Ecx:08x} EDX=0x{ctx.Edx:08x} ESP=0x{ctx.Esp:08x}')
                
                if exc_addr == 0x423019:
                    # [esp+4] is return addr, [esp+8] is filename ptr
                    arg_buf = (ctypes.c_byte * 4)()
                    kernel32.ReadProcessMemory(pi.hProcess, ctx.Esp + 4, arg_buf, 4, ctypes.byref(read))
                    arg1 = int.from_bytes(bytes(arg_buf), 'little')
                    str_buf = (ctypes.c_char * 64)()
                    kernel32.ReadProcessMemory(pi.hProcess, arg1, str_buf, 64, ctypes.byref(read))
                    print(f'     0x423019 Arg1 (file to find): {bytes(str_buf).split(b"\\x00")[0]}')

                elif exc_addr == 0x492fe5:
                    # Let's read [ebp - 0x36c] after wsprintf or read GetLastError from TEB
                    teb = ctx.SegFs # 0x18
                    pass

                # restore byte and step
                orig = (ctypes.c_byte * 1)(orig_bytes[exc_addr])
                kernel32.WriteProcessMemory(pi.hProcess, exc_addr, orig, 1, ctypes.byref(written))
                ctx.Eip = exc_addr
                kernel32.SetThreadContext(hThread, ctypes.byref(ctx))
                kernel32.CloseHandle(hThread)
            else:
                status = DBG_EXCEPTION_NOT_HANDLED
        kernel32.ContinueDebugEvent(de.dwProcessId, de.dwThreadId, status)

    kernel32.TerminateProcess(pi.hProcess, 0)

if __name__ == '__main__':
    main()
