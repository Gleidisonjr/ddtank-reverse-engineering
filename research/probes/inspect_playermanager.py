import sys
sys.path.append('scripts/probes')
from inspect_packet_internals import parse_abc
import struct

with open('targets/dd-classico/extracted/dumped/flash_assets/2.swf', 'rb') as f:
    raw = bytearray(f.read())
if raw[:3] == b'CWS':
    raw[:3] = b'FWS'

nbits = raw[8] >> 3
pos = 8 + (5 + nbits * 4 + 7) // 8 + 4

while pos < len(raw):
    tcl = struct.unpack('<H', raw[pos:pos+2])[0]
    pos += 2
    code, tlen = tcl >> 6, tcl & 0x3F
    if tlen == 0x3F:
        tlen = struct.unpack('<I', raw[pos:pos+4])[0]
        pos += 4
    if code == 82:
        d = raw[pos:pos+tlen]
        n_idx = d.find(b'\x00', 4)
        name = d[4:n_idx].decode('utf-8', errors='replace')
        if name == 'ddt/manager/PlayerManager':
            print("Found ddt/manager/PlayerManager!")
            insts, ctraits, methods, bodies, strings, ints, multinames = parse_abc(d[n_idx+1:])
            print(f"Total methods: {len(methods)}, bodies: {len(bodies)}")
            for inst in insts:
                for tname, tkind, mid in inst['traits']:
                    if mid in bodies:
                        # check if it references grid or bag or update
                        print(f"Inst Trait: {tname} (m_id={mid})")
            for ct in ctraits:
                for tname, tkind, val in ct['traits']:
                    print(f"Class Trait: {tname} = {val}")
    pos += tlen
