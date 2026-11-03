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
        if name == 'ddt/utils/StaticFormula':
            insts, ctraits, methods, bodies, strings, ints, multinames = parse_abc(d[n_idx+1:])
            for mid, mname in [(1, 'getHertAddition'), (2, 'getDefenseAddition'), (3, 'getRecoverHPAddition')]:
                body = bodies[mid]
                print(f"=== {mname} (m_id={mid}, len={len(body)}) ===")
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
                    elif op == 0x2F:
                        # pushdouble
                        d_idx = read_u30(); print(f"  {pc:04x}: pushdouble {d_idx}")
                    elif op == 0x66:
                        m = read_u30(); print(f"  {pc:04x}: getproperty {multinames[m] if m < len(multinames) else m}")
                    elif op == 0x61:
                        m = read_u30(); print(f"  {pc:04x}: setproperty {multinames[m] if m < len(multinames) else m}")
                    elif op == 0x46:
                        m = read_u30(); argc = read_u30(); print(f"  {pc:04x}: callproperty {multinames[m] if m < len(multinames) else m} (argc={argc})")
                    elif op == 0xA0: print(f"  {pc:04x}: add")
                    elif op == 0xA1: print(f"  {pc:04x}: subtract")
                    elif op == 0xA2: print(f"  {pc:04x}: multiply")
                    elif op == 0xA3: print(f"  {pc:04x}: divide")
                    elif op == 0x47: print(f"  {pc:04x}: returnvoid")
                    elif op == 0x48: print(f"  {pc:04x}: returnvalue")
                    elif op == 0xD0: print(f"  {pc:04x}: getlocal_0")
                    elif op == 0xD1: print(f"  {pc:04x}: getlocal_1")
                    elif op == 0xD2: print(f"  {pc:04x}: getlocal_2")
    pos += tlen
