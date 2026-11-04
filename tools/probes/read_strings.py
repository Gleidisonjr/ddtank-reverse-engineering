import pefile

pe = pefile.PE('targets/district-187/client-rebirth/TheRaw.exe')
vas = [0x7dc59c, 0x7dc574, 0x7dc550, 0x7dc52c, 0x7dc504, 0x7dc4d8, 0x7dc4c0, 0x7dc430, 0x7dc41c]

with open('targets/district-187/client-rebirth/TheRaw.exe', 'rb') as f:
    for va in vas:
        offset = pe.get_offset_from_rva(va - 0x400000)
        f.seek(offset)
        raw = f.read(60)
        s = raw.split(b'\x00')[0].decode(errors='ignore')
        print(f"VA {hex(va)}: '{s}'")
