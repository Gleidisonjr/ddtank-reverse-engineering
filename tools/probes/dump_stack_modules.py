import ctypes
from ctypes import wintypes
import os

kernel32 = ctypes.windll.kernel32

pid = 18536
hp = kernel32.OpenProcess(0x001F0FFF, False, pid)

# Get all modules of pid
import pefile

# Read stack
stack_buf = (ctypes.c_byte * 4096)()
read = ctypes.c_size_t()
kernel32.ReadProcessMemory(hp, 0x001afb44, stack_buf, 4096, ctypes.byref(read))
stack = [int.from_bytes(bytes(stack_buf)[i:i+4], 'little') for i in range(0, 4096, 4)]

# Find modules from /proc or toolhelp
TH32CS_SNAPMODULE = 0x00000008
class MODULEENTRY32(ctypes.Structure):
    _fields_ = [
        ('dwSize', wintypes.DWORD),
        ('th32ModuleID', wintypes.DWORD),
        ('th32ProcessID', wintypes.DWORD),
        ('GlblcntUsage', wintypes.DWORD),
        ('ProccntUsage', wintypes.DWORD),
        ('modBaseAddr', ctypes.c_void_p),
        ('modBaseSize', wintypes.DWORD),
        ('hModule', wintypes.HMODULE),
        ('szModule', ctypes.c_char * 256),
        ('szExePath', ctypes.c_char * 260),
    ]

h_snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE, pid)
me = MODULEENTRY32()
me.dwSize = ctypes.sizeof(me)
mods = []
if kernel32.Module32First(h_snap, ctypes.byref(me)):
    while True:
        mods.append((me.modBaseAddr, me.modBaseSize, me.szModule.decode(errors='ignore')))
        if not kernel32.Module32Next(h_snap, ctypes.byref(me)):
            break
kernel32.CloseHandle(h_snap)

for i, addr in enumerate(stack):
    for base, size, name in mods:
        if base <= addr < base + size:
            offset = addr - base
            # Filter common ntdll/kernelbase leaf frames
            print(f"[+0x{i*4:03x}] 0x{addr:08x} -> {name} + 0x{offset:x}")
            break
