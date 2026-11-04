"""
Generate Minimal Valid AS3 SWF Files and Fallbacks for DDTank Client
Author: Reverse Engineering Brain
Target: DDClássico (ddclassico.com) v2.0.5 / 7Road DDTank Engine
"""

import os
import struct

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
WWW_DIR = os.path.join(BASE_DIR, 'www')


def create_minimal_as3_swf(version=14, width=800, height=600):
    """
    Builds a 100% specification-compliant minimal ActionScript 3 SWF binary.
    Tag 69 (FileAttributes) has bit 3 set (0x08 = ActionScript 3).
    """
    twip_w = width * 20
    twip_h = height * 20
    max_val = max(twip_w, twip_h)
    nbits = max_val.bit_length() + 1

    total_bits = 5 + 4 * nbits
    total_bytes = (total_bits + 7) // 8
    bit_str = f'{nbits:05b}' + f'{0:0{nbits}b}' + f'{twip_w:0{nbits}b}' + f'{0:0{nbits}b}' + f'{twip_h:0{nbits}b}'
    bit_str = bit_str.ljust(total_bytes * 8, '0')
    rect = bytes(int(bit_str[i:i+8], 2) for i in range(0, len(bit_str), 8))

    fps = struct.pack('<H', 24 << 8)
    frame_count = struct.pack('<H', 1)

    # Tag 69: FileAttributes (AS3 = 0x08)
    tag_file_attrs = struct.pack('<HI', (69 << 6) | 4, 0x08)

    # Tag 1: ShowFrame
    tag_show_frame = struct.pack('<H', 1 << 6)

    # Tag 0: End
    tag_end = struct.pack('<H', 0)

    body = rect + fps + frame_count + tag_file_attrs + tag_show_frame + tag_end
    file_length = 8 + len(body)
    header = b'FWS' + bytes([version]) + struct.pack('<I', file_length)
    return header + body


def main():
    swf_bytes = create_minimal_as3_swf()

    target_paths = [
        os.path.join(WWW_DIR, 'flash', 'ui', 'swf', 'choicefigure.swf'),
        os.path.join(WWW_DIR, 'flash', 'ui', 'swf', 'roadcomponent.swf'),
        os.path.join(WWW_DIR, 'ui', 'swf', 'choicefigure.swf'),
        os.path.join(WWW_DIR, 'ui', 'swf', 'roadcomponent.swf'),
        os.path.join(WWW_DIR, 'flash', '3.png'),
        os.path.join(WWW_DIR, '3.png'),
    ]

    for path in target_paths:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            f.write(swf_bytes)
        print(f"[+] Created minimal AS3 SWF at: {path} ({len(swf_bytes)} bytes)")


if __name__ == '__main__':
    main()
