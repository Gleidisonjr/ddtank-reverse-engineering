import ctypes
from ctypes import wintypes
import traceback

try:
    d3d9 = ctypes.windll.d3d9
    d3d = d3d9.Direct3DCreate9(32)
    print("Direct3DCreate9 ptr:", hex(d3d))

    vtable = ctypes.cast(d3d, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents

    # COM methods use stdcall (__stdcall)
    GetAdapterCount = ctypes.WINFUNCTYPE(wintypes.UINT, ctypes.c_void_p)(vtable[4])
    num_adapters = GetAdapterCount(d3d)
    print("Num adapters:", num_adapters)

    class D3DADAPTER_IDENTIFIER9(ctypes.Structure):
        _fields_ = [
            ("Driver", ctypes.c_char * 512),
            ("Description", ctypes.c_char * 512),
            ("DeviceName", ctypes.c_char * 32),
            ("DriverVersion", wintypes.LARGE_INTEGER),
            ("VendorId", wintypes.DWORD),
            ("DeviceId", wintypes.DWORD),
            ("SubSysId", wintypes.DWORD),
            ("Revision", wintypes.DWORD),
            ("DeviceIdentifier", ctypes.c_byte * 16),
            ("WHQLLevel", wintypes.DWORD),
        ]

    GetAdapterIdentifier = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, wintypes.UINT, wintypes.DWORD, ctypes.POINTER(D3DADAPTER_IDENTIFIER9))(vtable[5])

    for a in range(num_adapters):
        ident = D3DADAPTER_IDENTIFIER9()
        hr = GetAdapterIdentifier(d3d, a, 0, ctypes.byref(ident))
        print(f"Adapter {a}: {ident.Description.decode('latin1', errors='ignore')} ({ident.DeviceName.decode('latin1', errors='ignore')})")

    CheckDeviceType = ctypes.WINFUNCTYPE(
        ctypes.c_long,
        ctypes.c_void_p,
        wintypes.UINT,
        wintypes.UINT,
        wintypes.UINT,
        wintypes.UINT,
        wintypes.BOOL
    )(vtable[9])

    for a in range(num_adapters):
        for dev_type in [1, 2]: # 1=HAL, 2=REF
            for fmt in [21, 22]: # 21=A8R8G8B8, 22=X8R8G8B8
                for win in [False, True]:
                    hr = CheckDeviceType(d3d, a, dev_type, fmt, fmt, win)
                    print(f"Adapter {a}, DevType {dev_type}, Fmt {fmt}, Win {win} -> HR: {hex(hr & 0xffffffff)}")

except Exception:
    traceback.print_exc()
