import pefile, struct, sys
sys.stdout.reconfigure(encoding='utf-8')

pe = pefile.PE(r"targets\district-187\client-rebirth\Game\GameClient.dll", fast_load=True)
image_base = pe.OPTIONAL_HEADER.ImageBase
with open(r"targets\district-187\client-rebirth\Game\GameClient.dll", "rb") as f:
    data = f.read()

def va_to_raw(va):
    rva = va - image_base
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (rva - s.VirtualAddress)
    return 0

def raw_to_va(raw):
    for s in pe.sections:
        if s.PointerToRawData <= raw < s.PointerToRawData + s.SizeOfRawData:
            return image_base + s.VirtualAddress + (raw - s.PointerToRawData)
    return 0

text_s = pe.sections[0]
t_start = text_s.PointerToRawData
t_end = t_start + text_s.SizeOfRawData

registrations = []
for off in range(t_start, t_end - 32):
    # look for 8B 42 2C (mov eax, [edx+0x2c]) or 8B 4A 2C or 8B 50 2C followed by 68 (push imm32)
    if data[off+3] == 0x68 and data[off+2] == 0x2c and data[off] == 0x8b:
        pkt_id = struct.unpack_from("<I", data, off + 4)[0]
        chunk = data[off-24:off]
        v_idx = chunk.rfind(b"\xc7\x00")
        if v_idx != -1 and (0x100000 <= pkt_id <= 0x999999):
            vt_va = struct.unpack_from("<I", chunk, v_idx + 2)[0]
            vt_raw = va_to_raw(vt_va)
            if vt_raw:
                fn0, fn1 = struct.unpack_from("<II", data, vt_raw)
                registrations.append((pkt_id, raw_to_va(off), vt_va, fn1))

registrations.sort()
print(f"Found {len(registrations)} packet handlers:")
for pkt_id, reg_va, vt_va, handler_va in registrations:
    if (pkt_id >> 16) in (0x11, 0x12, 0x21, 0x22, 0x23, 0x24, 0x25, 0x31, 0x41, 0x5A):
        print(f"PktID 0x{pkt_id:06x} | Reg @ 0x{reg_va:08x} | Vtable 0x{vt_va:08x} | Handler 0x{handler_va:08x}")
