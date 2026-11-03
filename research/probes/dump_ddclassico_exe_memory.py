import subprocess
import time
import os
import psutil
import ctypes
from ctypes import wintypes
import re

# Win32 API for memory scanning
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
MEM_COMMIT = 0x1000
PAGE_READONLY = 0x02
PAGE_READWRITE = 0x04
PAGE_EXECUTE_READ = 0x20
PAGE_EXECUTE_READWRITE = 0x40

class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD),
        ("PartitionId", wintypes.WORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", wintypes.DWORD),
        ("Protect", wintypes.DWORD),
        ("Type", wintypes.DWORD),
    ]

kernel32 = ctypes.windll.kernel32
VirtualQueryEx = kernel32.VirtualQueryEx
VirtualQueryEx.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.POINTER(MEMORY_BASIC_INFORMATION), ctypes.c_size_t]
VirtualQueryEx.restype = ctypes.c_size_t

ReadProcessMemory = kernel32.ReadProcessMemory
ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
ReadProcessMemory.restype = wintypes.BOOL

OpenProcess = kernel32.OpenProcess
OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
OpenProcess.restype = wintypes.HANDLE

CloseHandle = kernel32.CloseHandle
CloseHandle.argtypes = [wintypes.HANDLE]
CloseHandle.restype = wintypes.BOOL

def dump_memory_to_file(pid: int, output_file: str):
    hProcess = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not hProcess:
        print(f"[-] Could not open process {pid}: Error {ctypes.GetLastError()}")
        return False

    print(f"[+] Scanning and dumping all memory of PID {pid} to {output_file}...")
    mbi = MEMORY_BASIC_INFORMATION()
    address = 0
    max_addr = 0x7FFFFFFFFFFF

    total_dumped = 0
    with open(output_file, "wb") as out_f:
        while address < max_addr:
            if VirtualQueryEx(hProcess, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi)) == 0:
                break

            if mbi.State == MEM_COMMIT and (mbi.Protect & (PAGE_READONLY | PAGE_READWRITE | PAGE_EXECUTE_READ | PAGE_EXECUTE_READWRITE)):
                buf = (ctypes.c_char * mbi.RegionSize)()
                bytes_read = ctypes.c_size_t(0)
                if ReadProcessMemory(hProcess, ctypes.c_void_p(address), buf, mbi.RegionSize, ctypes.byref(bytes_read)):
                    out_f.write(bytes(buf[:bytes_read.value]))
                    total_dumped += bytes_read.value

            address += mbi.RegionSize

    CloseHandle(hProcess)
    print(f"[SUCCESS] Total dumped from RAM: {total_dumped / 1024 / 1024:.2f} MB")
    return True

if __name__ == "__main__":
    exe = os.path.abspath(r"targets\dd-classico\extracted\app\DDClassico.exe")
    app_dir = os.path.dirname(exe)
    env = os.environ.copy()
    env["__COMPAT_LAYER"] = "RunAsInvoker"

    print(f"[*] Launching {exe}...")
    p = subprocess.Popen([exe], cwd=app_dir, env=env)
    time.sleep(2.0)

    dump_path = os.path.abspath(r"targets\dd-classico\ddclassico_ram.dmp")
    try:
        dump_memory_to_file(p.pid, dump_path)
    finally:
        for proc in psutil.process_iter(['pid', 'name']):
            if 'ddclassico' in (proc.info['name'] or '').lower():
                proc.kill()
