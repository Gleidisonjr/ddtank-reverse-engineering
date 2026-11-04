import ctypes
from ctypes import wintypes
import sys

kernel32 = ctypes.windll.kernel32

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400

pid = 14940
h_proc = kernel32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)
if not h_proc:
    print('Failed to open process:', kernel32.GetLastError())
    sys.exit(1)

# In 32-bit process, GameClient.dll preferred base is 0x10000000 (ASLR is stripped/disabled on this binary!)
# Let's verify ASLR flag on GameClient.dll
va_ptr = 0x10522218
buf = ctypes.c_uint32()
read = ctypes.c_size_t()

res = kernel32.ReadProcessMemory(h_proc, ctypes.c_void_p(va_ptr), ctypes.byref(buf), 4, ctypes.byref(read))
print('ReadProcessMemory result:', res, 'bytes read:', read.value)
ptr1 = buf.value
print(f'Value at 0x{va_ptr:X}: 0x{ptr1:X}')

if ptr1:
    res = kernel32.ReadProcessMemory(h_proc, ctypes.c_void_p(ptr1 + 0x38), ctypes.byref(buf), 4, ctypes.byref(read))
    ptr2 = buf.value
    print(f'Value at ptr1 + 0x38 (0x{ptr1+0x38:X}): 0x{ptr2:X}')
    if ptr2:
        res = kernel32.ReadProcessMemory(h_proc, ctypes.c_void_p(ptr2 + 0x30), ctypes.byref(buf), 4, ctypes.byref(read))
        ptr3 = buf.value
        print(f'Value at ptr2 + 0x30 (0x{ptr2+0x30:X}): 0x{ptr3:X}')

kernel32.CloseHandle(h_proc)
