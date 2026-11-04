import ctypes
from ctypes import wintypes
import sys

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010

kernel32 = ctypes.windll.kernel32
psapi = ctypes.windll.psapi

pid = int(sys.argv[1]) if len(sys.argv) > 1 else 23716
hProcess = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
if not hProcess:
    print(f"Could not open process {pid}, error: {kernel32.GetLastError()}")
    sys.exit(1)

psapi.EnumProcessModules.argtypes = [wintypes.HANDLE, ctypes.POINTER(ctypes.c_void_p), wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
psapi.GetModuleFileNameExW.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.LPWSTR, wintypes.DWORD]

hMods = (ctypes.c_void_p * 1024)()
cbNeeded = wintypes.DWORD()
if psapi.EnumProcessModules(hProcess, hMods, ctypes.sizeof(hMods), ctypes.byref(cbNeeded)):
    count = cbNeeded.value // ctypes.sizeof(ctypes.c_void_p)
    print(f"Loaded modules ({count}):")
    for i in range(count):
        hMod = hMods[i]
        modName = ctypes.create_unicode_buffer(512)
        psapi.GetModuleFileNameExW(hProcess, hMod, modName, 512)
        print(f"  {hex(hMod or 0)}: {modName.value}")
else:
    print("EnumProcessModules failed")

kernel32.CloseHandle(hProcess)
