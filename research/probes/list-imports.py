import struct
import os

def list_imported_dlls(filepath):
    print(f"=== {os.path.basename(filepath)} ===")
    with open(filepath, "rb") as f:
        data = f.read()
    if data[:2] != b"MZ": return
    pe_off = struct.unpack_from("<I", data, 0x3C)[0]
    import_rva, import_size = struct.unpack_from("<II", data, pe_off + 24 + 80)
    if import_rva == 0: return

    num_sections = struct.unpack_from("<H", data, pe_off + 6)[0]
    opt_header_size = struct.unpack_from("<H", data, pe_off + 20)[0]
    section_offset = pe_off + 24 + opt_header_size

    def rva_to_off(rva):
        for i in range(num_sections):
            sec = section_offset + i * 40
            v_size, v_addr, r_size, r_offset = struct.unpack_from("<IIII", data, sec + 8)
            if v_addr <= rva < v_addr + max(v_size, r_size):
                return rva - v_addr + r_offset
        return None

    imp_off = rva_to_off(import_rva)
    if not imp_off: return

    idx = 0
    while True:
        entry = imp_off + idx * 20
        orig_first_thunk, ts, fwd, name_rva, first_thunk = struct.unpack_from("<IIIII", data, entry)
        if name_rva == 0: break
        idx += 1
        name_off = rva_to_off(name_rva)
        if not name_off: continue
        dll_name = ""
        while name_off < len(data) and data[name_off] != 0:
            dll_name += chr(data[name_off])
            name_off += 1
        print(f"  {repr(dll_name)}")

for p in [r"targets\district-187\client\S2\TheRaw.exe", r"targets\district-187\client\S2\Game\GameClient.dll", r"targets\district-187\client\S2\Engine_Server.dll"]:
    list_imported_dlls(p)
