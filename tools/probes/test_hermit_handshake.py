import struct
import binascii

# The 256-entry IEEE 802.3 CRC32 table from TheRaw.exe at VA 0x802a58
CRC_TABLE = []
for i in range(256):
    c = i
    for j in range(8):
        if c & 1:
            c = 0xEDB88320 ^ (c >> 1)
        else:
            c = c >> 1
    CRC_TABLE.append(c)

def encrypt_hermit_packet(plain_pkt: bytes, key_byte: int = 0x0F) -> bytes:
    """
    Encrypts a Hermit packet using the exact algorithm from TheRaw.exe (0x4ff470):
    C[i] = P[i] ^ (CRC_TABLE[i & 0xFF] & 0xFF) ^ key_byte (for i from 4 to len-1)
    CRC32 is computed over C[4:] and placed at C[0:4] in Big Endian.
    """
    buf = bytearray(plain_pkt)
    for i in range(4, len(buf)):
        tbl_byte = CRC_TABLE[i & 0xFF] & 0xFF
        buf[i] = plain_pkt[i] ^ tbl_byte ^ key_byte
    crc = binascii.crc32(buf[4:]) & 0xFFFFFFFF
    buf[0:4] = struct.pack('>I', crc)
    return bytes(buf)

def decrypt_hermit_packet(cipher_pkt: bytes, key_byte: int = 0x0F) -> tuple[bytes, bool]:
    """
    Decrypts a Hermit packet using the exact algorithm from TheRaw.exe (0x4ff660).
    Returns (decrypted_packet, crc_valid).
    """
    buf = bytearray(cipher_pkt)
    if len(buf) < 16:
        return bytes(buf), False
    expected_crc = struct.unpack('>I', buf[0:4])[0]
    actual_crc = binascii.crc32(buf[4:]) & 0xFFFFFFFF
    crc_valid = (expected_crc == actual_crc)

    for i in range(4, len(buf)):
        tbl_byte = CRC_TABLE[i & 0xFF] & 0xFF
        buf[i] = cipher_pkt[i] ^ tbl_byte ^ key_byte
    return bytes(buf), crc_valid

def test():
    # 1. Test decrypting the captured 20-byte packet from TheRaw.exe
    captured = bytes.fromhex('6cccdc7716803a8c39a8581524b0081f6bfd47d1')
    # wait, the captured packet was:
    # 6c cc dc 77 16 80 3a b8 39 a8 58 15 24 b0 08 1e 6b fd 47 d1
    cap_actual = bytes.fromhex('6cccdc7716803ab839a8581524b0081e6bfd47d1')
    dec, ok = decrypt_hermit_packet(cap_actual, 0x0F)
    print(f"Captured packet CRC valid: {ok}")
    print(f"Decrypted raw: {dec.hex()}")
    # Unpack header
    crc, flags, length, session_id, pkt_id = struct.unpack('>IHHII', dec[:16])
    print(f"Decrypted Header: CRC={hex(crc)}, Flags={hex(flags)}, Length={length}, Session={hex(session_id)}, PktID={hex(pkt_id)}")
    assert pkt_id == 0x20080
    assert length == 20

    # 2. Build Packet 0x20081 (Handshake Response, 32 bytes)
    payload_81 = struct.pack('>IIII', 0x12345678, 0, 0, 0x0F)
    header_81 = struct.pack('>HHII', 0, 32, session_id, 0x20081)
    plain_81 = b'\x00\x00\x00\x00' + header_81 + payload_81
    enc_81 = encrypt_hermit_packet(plain_81, 0x0F)
    print(f"\nConstructed 0x20081 Encrypted ({len(enc_81)} bytes): {enc_81.hex()}")

    dec_81, ok_81 = decrypt_hermit_packet(enc_81, 0x0F)
    print(f"0x20081 Decryption test CRC valid: {ok_81}")
    _, _, len_81, sess_81, id_81 = struct.unpack('>IHHII', dec_81[:16])
    print(f"0x20081 Decrypted Header: Length={len_81}, Session={hex(sess_81)}, PktID={hex(id_81)}")
    assert id_81 == 0x20081
    assert len_81 == 32

    # 3. Build Packet 0x20083 (Handshake Pong / ACK, 20 bytes)
    payload_83 = struct.pack('>I', 0)
    header_83 = struct.pack('>HHII', 0, 20, session_id, 0x20083)
    plain_83 = b'\x00\x00\x00\x00' + header_83 + payload_83
    enc_83 = encrypt_hermit_packet(plain_83, 0x0F)
    print(f"\nConstructed 0x20083 Encrypted ({len(enc_83)} bytes): {enc_83.hex()}")

    print("\n[+] All tests passed successfully!")

if __name__ == "__main__":
    test()
