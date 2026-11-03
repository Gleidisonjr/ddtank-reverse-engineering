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
        if name == 'ddt/data/EquipType':
            insts, ctraits, methods, bodies, strings, ints, multinames = parse_abc(d[n_idx+1:])
            # find CategeryIdToPlace method
            for ct in ctraits:
                for tn, tk, val in ct['traits']:
                    if tn in ('CategeryIdToPlace', 'placeToCategeryId'):
                        mid = val
                        print(f"=== {tn} (m_id={mid}) ===")
                        body = bodies[mid]
                        p = 0
                        def read_u30():
                            global p
                            res, shift = 0, 0
                            while True:
                                b = body[p]; p += 1
                                res |= (b & 0x7f) << shift
                                if (b & 0x80) == 0: break
                                shift += 7
                            return res
                        while p < len(body):
                            pc = p; op = body[p]; p += 1
                            if op == 0x24:
                                b = body[p]; p += 1; print(f"  {pc:04x}: pushbyte {b}")
                            elif op == 0x25:
                                s = read_u30(); print(f"  {pc:04x}: pushshort {s}")
                            elif op == 0x2D:
                                idx = read_u30(); print(f"  {pc:04x}: pushint {ints[idx] if idx < len(ints) else idx}")
                            elif op == 0x48: print(f"  {pc:04x}: returnvalue")
                            elif op == 0xD0: print(f"  {pc:04x}: getlocal_0")
                            elif op == 0xD1: print(f"  {pc:04x}: getlocal_1")
                            elif op == 0x14:
                                b0, b1, b2 = body[p], body[p+1], body[p+2]; p += 3
                                s24 = b0 | (b1 << 8) | (b2 << 16)
                                if s24 & 0x800000: s24 -= 0x1000000
                                print(f"  {pc:04x}: ifne {pc + 4 + s24:04x}")
                            elif op == 0x13:
                                b0, b1, b2 = body[p], body[p+1], body[p+2]; p += 3
                                s24 = b0 | (b1 << 8) | (b2 << 16)
                                if s24 & 0x800000: s24 -= 0x1000000
                                print(f"  {pc:04x}: ifeq {pc + 4 + s24:04x}")
                            elif op == 0x10:
                                b0, b1, b2 = body[p], body[p+1], body[p+2]; p += 3
                                s24 = b0 | (b1 << 8) | (b2 << 16)
                                if s24 & 0x800000: s24 -= 0x1000000
                                print(f"  {pc:04x}: jump {pc + 4 + s24:04x}")
                            elif op == 0x30: print(f"  {pc:04x}: pushscope")
    pos += tlen
