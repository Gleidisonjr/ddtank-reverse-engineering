import zlib

with open('projects/ddtank-server/www/flash/Loading.swf', 'rb') as f:
    data = f.read()

body = zlib.decompress(data[8:])
abc_pos = body.find(b'Loading\x00')
abc_data = body[abc_pos+8:]

# Let's find the exact method body of __onConfigLoadComplete
# Method starts at abc_data offset 291260
# Let's inspect the opcodes from 291260 to 291480
code = abc_data[291260:291480]

OPCODES = {
    0x02: "nop",
    0x03: "throw",
    0x04: "getsuper",
    0x08: "kill",
    0x09: "label",
    0x0A: "jump",
    0x0C: "ifnlt",
    0x0D: "ifnle",
    0x0E: "ifngt",
    0x0F: "ifnge",
    0x10: "jump",
    0x11: "iftrue",
    0x12: "iffalse",
    0x13: "ifeq",
    0x14: "ifne",
    0x15: "iflt",
    0x16: "ifle",
    0x17: "ifgt",
    0x18: "ifge",
    0x19: "ifstricteq",
    0x1A: "ifstrictne",
    0x20: "pushnull",
    0x21: "pushundefined",
    0x24: "pushbyte",
    0x25: "pushshort",
    0x26: "pushtrue",
    0x27: "pushfalse",
    0x28: "pushnan",
    0x2A: "pushstring",
    0x2C: "pushstring",
    0x2F: "pushint",
    0x30: "pushscope",
    0x40: "newfunction",
    0x41: "call",
    0x42: "construct",
    0x43: "callmethod",
    0x44: "callstatic",
    0x45: "callsuper",
    0x46: "callproperty",
    0x47: "returnvoid",
    0x48: "returnvalue",
    0x49: "constructsuper",
    0x4A: "constructprop",
    0x4C: "callproplex",
    0x4E: "callsupervoid",
    0x4F: "callpropvoid",
    0x55: "newobject",
    0x56: "newarray",
    0x57: "newactivation",
    0x58: "newclass",
    0x59: "getdescendants",
    0x5A: "newcatch",
    0x5D: "findpropstrict",
    0x5E: "findproperty",
    0x60: "getlex",
    0x61: "setproperty",
    0x62: "getlocal",
    0x63: "setlocal",
    0x66: "getproperty",
    0x68: "initproperty",
    0x70: "setsuper",
    0x71: "getproperty",
    0x80: "coerce",
    0x82: "coerce_a",
    0x85: "coerce_s",
    0x86: "astype",
    0x87: "astypelate",
    0xA0: "add",
    0xA1: "subtract",
    0xA2: "multiply",
    0xA3: "divide",
    0xD0: "getlocal_0",
    0xD1: "getlocal_1",
    0xD2: "getlocal_2",
    0xD3: "getlocal_3",
}

i = 0
while i < len(code):
    b = code[i]
    name = OPCODES.get(b, f"0x{b:02x}")
    print(f"{i:3d}: {name} ({b:02x})")
    i += 1
