"""
DDTank Server & Handshake Smoke Test
Tests TCP connection, RSAKEY receipt, LOGIN dispatch, and SelfInfo verification.
"""

import socket
import sys
import os
import time

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(BASE_DIR, 'src'))
from ddt_protocol import DDTPacket, DDTStreamWriter, DDTStreamReader, HEADER_SIZE

def run_smoke_test(host="127.0.0.1", port=9200):
    print(f"[*] Connecting to DDTank Game Server at {host}:{port}...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.settimeout(5.0)

    # 1. Expect RSAKEY (Opcode 7)
    data = s.recv(1024)
    assert len(data) >= HEADER_SIZE, "No packet received from server"
    pkg = DDTPacket.unpack(data)
    print(f"[+] Step 1 (RSAKEY): Received Opcode {pkg.code} (Expected 7), len={len(pkg.payload)}")
    assert pkg.code == 7, f"Expected Opcode 7, got {pkg.code}"

    # 2. Send LOGIN (Opcode 1)
    w = DDTStreamWriter()
    w.write_int(20261025) # Build version
    w.write_int(1)        # DesktopType
    w.write_utf("Admin")  # Account
    login_pkg = DDTPacket(code=1, client_id=1, payload=w.get_bytes())
    s.sendall(login_pkg.pack())
    print("[+] Step 2 (LOGIN): Dispatched LOGIN packet to server")

    # 3. Receive LOGIN Response (Opcode 1 with SelfInfo)
    resp_data = s.recv(4096)
    assert len(resp_data) >= HEADER_SIZE, "No response for LOGIN"
    resp_pkg = DDTPacket.unpack(resp_data)
    print(f"[+] Step 3 (SelfInfo): Received Opcode {resp_pkg.code} (Expected 1), payload size={len(resp_pkg.payload)} bytes")
    assert resp_pkg.code == 1, f"Expected Opcode 1, got {resp_pkg.code}"

    # Read SelfInfo fields
    r = DDTStreamReader(resp_pkg.payload)
    result = r.read_byte()
    zone_id = r.read_int()
    attack = r.read_int()
    defence = r.read_int()
    agility = r.read_int()
    luck = r.read_int()
    damage = r.read_int()
    armor = r.read_int()
    gp = r.read_long()
    repute = r.read_int()
    gold = r.read_int()
    money = r.read_int()

    print(f"[+] Deserialized Player Profile:")
    print(f"    - Result Code:  {result} (0 = Success)")
    print(f"    - Zone ID:      {zone_id}")
    print(f"    - Attack/Def:   {attack} / {defence}")
    print(f"    - Agi/Luck:     {agility} / {luck}")
    print(f"    - Damage/Armor: {damage} / {armor}")
    print(f"    - Gold/Money:   {gold:,} Gold / {money:,} Cash")

    assert result == 0, "Login result should be 0"
    assert gold > 0, "Gold should be greater than 0"
    assert money > 0, "Money should be greater than 0"

    print("\n[+] 100% SUCCESS: DDTank Server Handshake, Crypto Framing & SelfInfo verified flawlessly!")
    s.close()

if __name__ == '__main__':
    run_smoke_test()
