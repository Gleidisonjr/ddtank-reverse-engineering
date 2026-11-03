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
            insts, ctraits, methods, bodies, strings, ints, multinames = parse_abc(d[n_idx+1:])
            body = bodies[70] # __updatePlayerInfo
            print(f"Disassembling __updatePlayerInfo (len={len(body)})")
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
                if op == 0x66:
                    m = read_u30(); print(f"  {pc:04x}: getproperty {multinames[m]}")
                elif op == 0x61:
                    m = read_u30(); print(f"  {pc:04x}: setproperty {multinames[m]}")
                elif op == 0x46:
                    m = read_u30(); argc = read_u30(); print(f"  {pc:04x}: callproperty {multinames[m]} (argc={argc})")
                elif op == 0x4F:
                    m = read_u30(); argc = read_u30(); print(f"  {pc:04x}: callpropvoid {multinames[m]} (argc={argc})")
                elif op == 0x5D:
                    m = read_u30(); print(f"  {pc:04x}: findpropstrict {multinames[m]}")
                elif op == 0x47: print(f"  {pc:04x}: returnvoid")
    pos += tlen
