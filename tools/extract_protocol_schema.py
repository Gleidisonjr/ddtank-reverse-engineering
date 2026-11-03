import struct
import json
import os
import sys

# Add probes path to import parse_abc
sys.path.append(os.path.join(os.path.dirname(__file__), 'probes'))
from inspect_packet_internals import parse_abc

def extract_all_protocol_schemas(swf_path, output_json_path):
    print(f'[*] Reading {swf_path}...')
    with open(swf_path, 'rb') as f:
        raw = bytearray(f.read())
    if raw[:3] == b'CWS':
        raw[:3] = b'FWS'

    nbits = raw[8] >> 3
    pos = 8 + (5 + nbits * 4 + 7) // 8 + 4

    abc_blocks = {}
    while pos < len(raw):
        if pos + 2 > len(raw): break
        tcl = struct.unpack('<H', raw[pos:pos+2])[0]
        pos += 2
        code, tlen = tcl >> 6, tcl & 0x3F
        if tlen == 0x3F:
            if pos + 4 > len(raw): break
            tlen = struct.unpack('<I', raw[pos:pos+4])[0]
            pos += 4
        if code == 82: # DoABC
            d = raw[pos:pos+tlen]
            null_idx = d.find(b'\x00', 4)
            name = d[4:null_idx].decode('utf-8', errors='replace')
            if 'packagetype' in name.lower() or 'socket' in name.lower():
                abc_blocks[name] = d[null_idx+1:]
        pos += tlen

    print(f'[*] Found {len(abc_blocks)} relevant ABC blocks.')

    schema = {
        'metadata': {
            'target': 'DDClássico (ddclassico.com) v2.0.5',
            'swf_source': '2.swf (decompressed 2.png, 7.27 MB)',
            'header_magic': '0x71AB (29099)',
            'header_size': 20,
            'default_cipher_key': [0xAE, 0xBF, 0x56, 0x78, 0xAB, 0xCD, 0xEF, 0xF1],
            'checksum_algorithm': 'sum(buffer[6:]) + 119 & 0x7F7F',
            'cipher_algorithm': 'Rolling byte XOR with dynamic key mutation: key[i%8] = (key[i%8] + prev_byte) ^ i'
        },
        'packet_types': {}
    }

    total_constants = 0
    for name, abc in sorted(abc_blocks.items(), key=lambda x: x[0]):
        try:
            insts, ctraits, methods, bodies, strings, ints, multinames = parse_abc(abc)
            for i, ct in enumerate(ctraits):
                cname = insts[i]['name'] if i < len(insts) else name
                constants = {}
                for tname, tkind, val in ct['traits']:
                    if val is not None:
                        constants[tname] = {
                            'value': val,
                            'hex': hex(val) if isinstance(val, int) else None
                        }
                if constants:
                    schema['packet_types'][name] = {
                        'class_name': cname,
                        'constants_count': len(constants),
                        'constants': constants
                    }
                    total_constants += len(constants)
        except Exception as e:
            print(f'[-] Error parsing {name}: {e}')

    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

    print(f'[+] Extracted {len(schema["packet_types"])} classes with {total_constants} total protocol constants!')
    print(f'[+] Saved schema to {output_json_path}')

    return schema

if __name__ == '__main__':
    swf = r'targets/dd-classico/extracted/dumped/flash_assets/2.swf'
    out_json = r'targets/dd-classico/data/ddt_protocol_schema.json'
    schema = extract_all_protocol_schemas(swf, out_json)
    
    print('\n=== Top Packet Type Categories ===')
    for cat, data in sorted(schema['packet_types'].items(), key=lambda x: x[1]['constants_count'], reverse=True)[:15]:
        print(f"  {cat:55} : {data['constants_count']} opcodes/constants")
