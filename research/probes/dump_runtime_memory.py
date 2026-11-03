import subprocess
import time
import os
import sys
import psutil
import ctypes
from ctypes import wintypes
import re

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

def dump_process_memory(pid: int) -> bytearray:
    hProcess = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not hProcess:
        print(f"[-] Could not open process {pid}: Error {ctypes.GetLastError()}")
        return bytearray()

    mbi = MEMORY_BASIC_INFORMATION()
    address = 0
    max_addr = 0x7FFFFFFFFFFF
    dump = bytearray()

    valid_protect = PAGE_READONLY | PAGE_READWRITE | PAGE_EXECUTE_READ | PAGE_EXECUTE_READWRITE

    while address < max_addr:
        if VirtualQueryEx(hProcess, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi)) == 0:
            break

        if mbi.State == MEM_COMMIT and (mbi.Protect & valid_protect):
            buf = (ctypes.c_char * mbi.RegionSize)()
            bytes_read = ctypes.c_size_t(0)
            if ReadProcessMemory(hProcess, ctypes.c_void_p(address), buf, mbi.RegionSize, ctypes.byref(bytes_read)):
                if bytes_read.value > 0:
                    dump.extend(bytes(buf[:bytes_read.value]))

        address += mbi.RegionSize

    CloseHandle(hProcess)
    return dump

def main():
    exe = os.path.abspath(r"targets\dd-classico\extracted\app\DDClassico.exe")
    app_dir = os.path.dirname(exe)
    out_dir = os.path.abspath(r"targets\dd-classico\extracted\dumped")
    os.makedirs(out_dir, exist_ok=True)

    env = os.environ.copy()
    env["__COMPAT_LAYER"] = "RunAsInvoker"

    print(f"[*] Launching {exe}...")
    launcher_proc = subprocess.Popen([exe], cwd=app_dir, env=env)
    print(f"[+] Launcher PID: {launcher_proc.pid}")

    runtime_main_pid = None
    runtime_renderer_pid = None

    try:
        # Wait up to 5 seconds for runtime processes
        for _ in range(10):
            time.sleep(0.5)
            for p in psutil.process_iter(['pid', 'name', 'cmdline', 'ppid']):
                try:
                    name = (p.info['name'] or '').lower()
                    if 'ddclassico.runtime' in name:
                        cmd = ' '.join(p.info['cmdline'] or [])
                        if '--type=renderer' in cmd:
                            runtime_renderer_pid = p.info['pid']
                        elif '--type=' not in cmd:
                            runtime_main_pid = p.info['pid']
                except Exception:
                    pass
            if runtime_main_pid and runtime_renderer_pid:
                break

        print(f"[+] Found Runtime Main PID: {runtime_main_pid}")
        print(f"[+] Found Runtime Renderer PID: {runtime_renderer_pid}")

        # Let the runtime fully initialize UI and decrypt launcher.pack
        time.sleep(2.0)

        # Dump Main Runtime
        if runtime_main_pid:
            print(f"[*] Dumping Runtime Main (PID {runtime_main_pid})...")
            main_mem = dump_process_memory(runtime_main_pid)
            print(f"[+] Main dump size: {len(main_mem) / 1024 / 1024:.2f} MB")
            with open(os.path.join(out_dir, "runtime_main_dump.bin"), "wb") as f:
                f.write(main_mem)

        # Dump Renderer Runtime
        if runtime_renderer_pid:
            print(f"[*] Dumping Runtime Renderer (PID {runtime_renderer_pid})...")
            renderer_mem = dump_process_memory(runtime_renderer_pid)
            print(f"[+] Renderer dump size: {len(renderer_mem) / 1024 / 1024:.2f} MB")
            with open(os.path.join(out_dir, "runtime_renderer_dump.bin"), "wb") as f:
                f.write(renderer_mem)

    finally:
        print("[*] Terminating processes...")
        for p in psutil.process_iter(['pid', 'name']):
            try:
                if 'ddclassico' in (p.info['name'] or '').lower():
                    p.kill()
            except Exception:
                pass

    print("[+] Done dumping RAM. Proceeding to scan & extract files.")

if __name__ == "__main__":
    main()
