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
            body = bodies[8] # __updateInventorySlot
            
            p = 0
            def read_u30():
                global p
                res, shift = 0, 0
                while True:
                    b = body[p]
                    p += 1
                    res |= (b & 0x7f) << shift
                    if (b & 0x80) == 0: break
                    shift += 7
                return res

            print(f"Disassembling PlayerManager::__updateInventorySlot (len={len(body)}):")
            while p < len(body):
                pc = p
                op = body[p]
                p += 1
                
                if op == 0x24: # pushbyte
                    b = body[p]; p += 1
                    print(f"  {pc:04x}: pushbyte {b}")
                elif op == 0x25: # pushshort
                    s = read_u30()
                    print(f"  {pc:04x}: pushshort {s}")
                elif op == 0x2C: # pushstring
                    s_idx = read_u30()
                    print(f"  {pc:04x}: pushstring \"{strings[s_idx] if s_idx < len(strings) else s_idx}\"")
                elif op == 0x26:
                    print(f"  {pc:04x}: pushtrue")
                elif op == 0x27:
                    print(f"  {pc:04x}: pushfalse")
                elif op == 0x20:
                    print(f"  {pc:04x}: pushnull")
                elif op == 0x21:
                    print(f"  {pc:04x}: pushundefined")
                elif op == 0xD0:
                    print(f"  {pc:04x}: getlocal_0 (this)")
                elif op == 0xD1:
                    print(f"  {pc:04x}: getlocal_1 (event/pkg)")
                elif op == 0xD2:
                    print(f"  {pc:04x}: getlocal_2")
                elif op == 0xD3:
                    print(f"  {pc:04x}: getlocal_3")
                elif op == 0xD4:
                    print(f"  {pc:04x}: setlocal_0")
                elif op == 0xD5:
                    print(f"  {pc:04x}: setlocal_1")
                elif op == 0xD6:
                    print(f"  {pc:04x}: setlocal_2")
                elif op == 0xD7:
                    print(f"  {pc:04x}: setlocal_3")
                elif op == 0x62: # getlocal
                    l = read_u30()
                    print(f"  {pc:04x}: getlocal {l}")
                elif op == 0x63: # setlocal
                    l = read_u30()
                    print(f"  {pc:04x}: setlocal {l}")
                elif op == 0x60: # getlex
                    m = read_u30()
                    print(f"  {pc:04x}: getlex {multinames[m] if m < len(multinames) else m}")
                elif op == 0x66: # getproperty
                    m = read_u30()
                    print(f"  {pc:04x}: getproperty {multinames[m] if m < len(multinames) else m}")
                elif op == 0x61: # setproperty
                    m = read_u30()
                    print(f"  {pc:04x}: setproperty {multinames[m] if m < len(multinames) else m}")
                elif op == 0x68: # initproperty
                    m = read_u30()
                    print(f"  {pc:04x}: initproperty {multinames[m] if m < len(multinames) else m}")
                elif op == 0x46: # callproperty
                    m = read_u30()
                    argc = read_u30()
                    print(f"  {pc:04x}: callproperty {multinames[m] if m < len(multinames) else m} (argc={argc})")
                elif op == 0x4F: # callpropvoid
                    m = read_u30()
                    argc = read_u30()
                    print(f"  {pc:04x}: callpropvoid {multinames[m] if m < len(multinames) else m} (argc={argc})")
                elif op == 0x5D: # findpropstrict
                    m = read_u30()
                    print(f"  {pc:04x}: findpropstrict {multinames[m] if m < len(multinames) else m}")
                elif op == 0x5E: # findproperty
                    m = read_u30()
                    print(f"  {pc:04x}: findproperty {multinames[m] if m < len(multinames) else m}")
                elif op == 0x47:
                    print(f"  {pc:04x}: returnvoid")
                elif op == 0x48:
                    print(f"  {pc:04x}: returnvalue")
                elif op == 0x12: # iftrue
                    b0, b1, b2 = body[p], body[p+1], body[p+2]
                    p += 3
                    s24 = b0 | (b1 << 8) | (b2 << 16)
                    if s24 & 0x800000: s24 -= 0x1000000
                    print(f"  {pc:04x}: iftrue {pc + 4 + s24:04x}")
                elif op == 0x11: # iffalse
                    b0, b1, b2 = body[p], body[p+1], body[p+2]
                    p += 3
                    s24 = b0 | (b1 << 8) | (b2 << 16)
                    if s24 & 0x800000: s24 -= 0x1000000
                    print(f"  {pc:04x}: iffalse {pc + 4 + s24:04x}")
                elif op == 0x0F: # ifne
                    b0, b1, b2 = body[p], body[p+1], body[p+2]
                    p += 3
                    s24 = b0 | (b1 << 8) | (b2 << 16)
                    if s24 & 0x800000: s24 -= 0x1000000
                    print(f"  {pc:04x}: ifne {pc + 4 + s24:04x}")
                elif op == 0x13: # ifeq
                    b0, b1, b2 = body[p], body[p+1], body[p+2]
                    p += 3
                    s24 = b0 | (b1 << 8) | (b2 << 16)
                    if s24 & 0x800000: s24 -= 0x1000000
                    print(f"  {pc:04x}: ifeq {pc + 4 + s24:04x}")
                elif op == 0x14: # iflt
                    b0, b1, b2 = body[p], body[p+1], body[p+2]
                    p += 3
                    s24 = b0 | (b1 << 8) | (b2 << 16)
                    if s24 & 0x800000: s24 -= 0x1000000
                    print(f"  {pc:04x}: iflt {pc + 4 + s24:04x}")
                elif op == 0x15: # ifge
                    b0, b1, b2 = body[p], body[p+1], body[p+2]
                    p += 3
                    s24 = b0 | (b1 << 8) | (b2 << 16)
                    if s24 & 0x800000: s24 -= 0x1000000
                    print(f"  {pc:04x}: ifge {pc + 4 + s24:04x}")
                elif op == 0x10: # jump
                    b0, b1, b2 = body[p], body[p+1], body[p+2]
                    p += 3
                    s24 = b0 | (b1 << 8) | (b2 << 16)
                    if s24 & 0x800000: s24 -= 0x1000000
                    print(f"  {pc:04x}: jump {pc + 4 + s24:04x}")
                elif op == 0x2A: # dup
                    print(f"  {pc:04x}: dup")
                elif op == 0x29: # pop
                    print(f"  {pc:04x}: pop")
                elif op == 0x30:
                    print(f"  {pc:04x}: pushscope")
                elif op == 0x1D:
                    print(f"  {pc:04x}: popscope")
                elif op == 0x5A:
                    print(f"  {pc:04x}: newactivation")
                elif op == 0x4A: # constructprop
                    m = read_u30()
                    argc = read_u30()
                    print(f"  {pc:04x}: constructprop {multinames[m] if m < len(multinames) else m} (argc={argc})")
                elif op == 0x80: # coerce
                    m = read_u30()
                    print(f"  {pc:04x}: coerce {multinames[m] if m < len(multinames) else m}")
                elif op == 0x82:
                    print(f"  {pc:04x}: coerce_a")
                elif op == 0x86:
                    print(f"  {pc:04x}: coerce_s")
                elif op == 0x87:
                    print(f"  {pc:04x}: coerce_d")
                elif op == 0x73:
                    print(f"  {pc:04x}: convert_i")
                elif op == 0x76:
                    print(f"  {pc:04x}: convert_b")
                elif op == 0x74:
                    print(f"  {pc:04x}: convert_u")
                elif op == 0x70:
                    print(f"  {pc:04x}: convert_s")
                elif op == 0x65: # getslot
                    s = read_u30()
                    print(f"  {pc:04x}: getslot {s}")
                elif op == 0x6D: # setslot
                    s = read_u30()
                    print(f"  {pc:04x}: setslot {s}")
                elif op == 0x6C: # getglobalslot
                    s = read_u30()
                    print(f"  {pc:04x}: getglobalslot {s}")
                elif op == 0xA0:
                    print(f"  {pc:04x}: add")
                elif op == 0xA1:
                    print(f"  {pc:04x}: subtract")
                elif op == 0xAB:
                    print(f"  {pc:04x}: equals")
                elif op == 0xAC:
                    print(f"  {pc:04x}: nequals")
                elif op == 0xB0:
                    print(f"  {pc:04x}: strictequals")
                else:
                    print(f"  {pc:04x}: unk_0x{op:02x}")
            break
    pos += tlen
