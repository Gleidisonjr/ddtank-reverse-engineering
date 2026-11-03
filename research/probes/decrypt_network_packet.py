import os
import sys
import hashlib

sys.stdout.reconfigure(encoding='utf-8')

def rc4(key: bytes, data: bytes) -> bytes:
    S = list(range(256))
    j = 0
    out = bytearray(len(data))
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) & 0xFF
        S[i], S[j] = S[j], S[i]
    i = j = 0
    for idx, char in enumerate(data):
        i = (i + 1) & 0xFF
        j = (j + S[i]) & 0xFF
        S[i], S[j] = S[j], S[i]
        out[idx] = char ^ S[(S[i] + S[j]) & 0xFF]
    return bytes(out)

TRAFFIC_PATH = r'targets/district-187/traffic/20261102_194718_031248_TCP.bin'
with open(TRAFFIC_PATH, 'rb') as f:
    ciphertext = f.read()

print(f"[*] Target Ciphertext ({len(ciphertext)} bytes): {ciphertext.hex()}")

CANDIDATE_KEYS = [
    b"S2", b"S2Online", b"District187", b"Doobic", b"DoobicGames",
    b"Joygame", b"Netmarble", b"CJInternet", b"Hermit", b"S2Rebirth",
    b"ApexGuard", b"Local\\ApexRing_", b"ApexRing_", b"179.61.147.154",
    b"12000", b"mdcreative", b"gamefiles.mdcreative.tr", b"gamefileshd.mdcreative.tr",
    b"LithTech", b"JupiterEX", b"TheRaw", b"GameClient", b"D187_SESSION_KEY",
    b"kurulum", b"Turkish", b"English", b"Apex", b"0x6801", b"2026-11-02",
]

def extract_strings(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()
    import re
    matches = re.findall(rb'[a-zA-Z0-9_\-\.]{4,32}', data)
    return set(matches)

for p in [r'targets/district-187/client-rebirth/TheRaw.exe', r'targets/district-187/client-rebirth/Game/GameClient.dll']:
    for s in extract_strings(p):
        if any(k in s.lower() for k in [b'key', b'crypt', b'pass', b'salt', b'seed', b'secret', b'auth', b's2', b'packet']):
            CANDIDATE_KEYS.append(s)

print(f"[*] Testing {len(CANDIDATE_KEYS)} candidate keys...")

found = False
for key in CANDIDATE_KEYS:
    # 1. Direct RC4
    try:
        p1 = rc4(key, ciphertext)
        pkt_len = int.from_bytes(p1[:2], 'little')
        if pkt_len == len(ciphertext) or p1[:4] == b'\x14\x00\x00\x00' or b'S2' in p1:
            print(f"[!] Direct RC4 match with key '{key.decode('latin1', errors='ignore')}':")
            print(f"    Hex: {p1.hex()}")
            print(f"    ASCII: {p1}")
            found = True
    except Exception:
        pass

    # 2. MD5-derived RC4 (Windows CryptoAPI CryptDeriveKey default)
    try:
        h = hashlib.md5(key).digest()
        p2 = rc4(h, ciphertext)
        pkt_len2 = int.from_bytes(p2[:2], 'little')
        if pkt_len2 == len(ciphertext) or p2[:4] == b'\x14\x00\x00\x00' or b'S2' in p2:
            print(f"[!] MD5-derived RC4 match with key '{key.decode('latin1', errors='ignore')}':")
            print(f"    Hex: {p2.hex()}")
            print(f"    ASCII: {p2}")
            found = True
    except Exception:
        pass

if not found:
    print("[-] No dictionary match on length == 20. Checking single-byte XOR...")
    for k in range(256):
        xored = bytes([b ^ k for b in ciphertext])
        pkt_len = int.from_bytes(xored[:2], 'little')
        if pkt_len == 20:
            print(f"[!] Single-byte XOR key 0x{k:02x}: {xored.hex()} | ASCII: {xored}")
            found = True

print("[*] Scan complete.")
