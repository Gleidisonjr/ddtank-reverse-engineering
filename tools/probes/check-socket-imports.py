import os
import struct

def check_socket_imports(filepath):
    with open(filepath, "rb") as f:
        data = f.read()
    if data[:2] != b"MZ": return
    pe_off = struct.unpack_from("<I", data, 0x3C)[0]
    opt_magic = struct.unpack_from("<H", data, pe_off + 24)[0]
    is_64 = (opt_magic == 0x20b)
    import_rva, import_size = struct.unpack_from("<II", data, pe_off + 24 + (104 if is_64 else 80))
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
        if not name_off or name_off >= len(data): continue
        dll_name = ""
        while name_off < len(data) and data[name_off] != 0:
            dll_name += chr(data[name_off])
            name_off += 1

        if "ws" in dll_name.lower() or "sock" in dll_name.lower():
            print(f"=== {os.path.basename(filepath)} imports {dll_name} ===")
            thunk_rva = orig_first_thunk if orig_first_thunk else first_thunk
            t_off = rva_to_off(thunk_rva)
            while True:
                val = struct.unpack_from("<I", data, t_off)[0]
                if val == 0: break
                t_off += 4
                if val & 0x80000000:
                    print(f"  Ordinal {val & 0xFFFF}")
                else:
                    fn_off = rva_to_off(val) + 2
                    fn_name = ""
                    while data[fn_off] != 0:
                        fn_name += chr(data[fn_off])
                        fn_off += 1
                    print(f"  {fn_name}")

client_dir = r"targets\district-187\client\S2"
for root, dirs, files in os.walk(client_dir):
    for f in files:
        if f.lower().endswith((".exe", ".dll")):
            check_socket_imports(os.path.join(root, f))
