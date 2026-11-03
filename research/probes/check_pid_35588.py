import ctypes
from ctypes import wintypes

kernel32 = ctypes.windll.kernel32
TH32CS_SNAPTHREAD = 0x00000004
class THREADENTRY32(ctypes.Structure):
    _fields_ = [
        ('dwSize', wintypes.DWORD),
        ('cntUsage', wintypes.DWORD),
        ('th32ThreadID', wintypes.DWORD),
        ('th32OwnerProcessID', wintypes.DWORD),
        ('tpBasePri', wintypes.LONG),
        ('tpDeltaPri', wintypes.LONG),
        ('dwFlags', wintypes.DWORD),
    ]

import sys
pid = int(sys.argv[1]) if len(sys.argv) > 1 else 35588
h_snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0)
te = THREADENTRY32()
te.dwSize = ctypes.sizeof(te)

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

hp = kernel32.OpenProcess(0x001F0FFF, False, pid)

if kernel32.Thread32First(h_snap, ctypes.byref(te)):
    while True:
        if te.th32OwnerProcessID == pid:
            tid = te.th32ThreadID
            ht = kernel32.OpenThread(0x001F03FF, False, tid)
            if ht:
                kernel32.SuspendThread(ht)
                ctx = WOW64_CONTEXT()
                ctx.ContextFlags = 0x10007 # FULL
                kernel32.Wow64GetThreadContext(ht, ctypes.byref(ctx))
                kernel32.ResumeThread(ht)
                print(f"Thread {tid}: EIP=0x{ctx.Eip:08x}, ESP=0x{ctx.Esp:08x}, EBP=0x{ctx.Ebp:08x}")
                
                # Read top of stack
                buf = (ctypes.c_byte * 64)()
                rd = ctypes.c_size_t()
                kernel32.ReadProcessMemory(hp, ctx.Esp, buf, 64, ctypes.byref(rd))
                dwords = [int.from_bytes(bytes(buf)[k:k+4], 'little') for k in range(0, 64, 4)]
                print("   Stack:", [hex(w) for w in dwords[:8]])
                kernel32.CloseHandle(ht)
        if not kernel32.Thread32Next(h_snap, ctypes.byref(te)):
            break
kernel32.CloseHandle(h_snap)
