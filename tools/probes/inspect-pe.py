import struct
import sys
import os

def parse_pe_exports(filepath):
    print(f"=== {os.path.basename(filepath)} ===")
    with open(filepath, "rb") as f:
        data = f.read()

    if data[:2] != b"MZ":
        print("Not an MZ file")
        return

    pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe_offset:pe_offset+4] != b"PE\0\0":
        print("Not a PE file")
        return

    opt_magic = struct.unpack_from("<H", data, pe_offset + 24)[0]
    is_64 = (opt_magic == 0x20b)
    export_table_offset = pe_offset + 24 + (112 if is_64 else 96)
    export_rva, export_size = struct.unpack_from("<II", data, export_table_offset)

    if export_rva == 0 or export_size == 0:
        print("No export table")
        return

    # Find section containing export_rva
    num_sections = struct.unpack_from("<H", data, pe_offset + 6)[0]
    opt_header_size = struct.unpack_from("<H", data, pe_offset + 20)[0]
    section_offset = pe_offset + 24 + opt_header_size

    def rva_to_offset(rva):
        for i in range(num_sections):
            sec = section_offset + i * 40
            v_size, v_addr, r_size, r_offset = struct.unpack_from("<IIII", data, sec + 8)
            if v_addr <= rva < v_addr + max(v_size, r_size):
                return rva - v_addr + r_offset
        return None

    exp_file_off = rva_to_offset(export_rva)
    if not exp_file_off:
        print("Could not map export RVA")
        return

    num_funcs, num_names, funcs_rva, names_rva, ords_rva = struct.unpack_from("<IIIII", data, exp_file_off + 20)
    names_off = rva_to_offset(names_rva)
    ords_off = rva_to_offset(ords_rva)
    funcs_off = rva_to_offset(funcs_rva)

    print(f"Export count: {num_names}")
    for i in range(min(num_names, 40)):
        name_rva = struct.unpack_from("<I", data, names_off + i * 4)[0]
        n_off = rva_to_offset(name_rva)
        name = ""
        while data[n_off] != 0:
            name += chr(data[n_off])
            n_off += 1
        ord_val = struct.unpack_from("<H", data, ords_off + i * 2)[0]
        func_rva = struct.unpack_from("<I", data, funcs_off + ord_val * 4)[0]
        print(f"  [{i}] {name} (RVA 0x{func_rva:08X})")

if __name__ == "__main__":
    for p in sys.argv[1:]:
        parse_pe_exports(p)
