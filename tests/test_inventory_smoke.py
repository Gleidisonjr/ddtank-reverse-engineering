"""
Automated Smoke Test for DDTank Core Server & Inventory/VIP Arsenal (Phase 3)
Target: DDClássico (ddclassico.com) v2.0.5 / 7Road DDTank Engine
Verifies TCP Connect, RSA Handshake, LOGIN SelfInfo, and GRID_GOODS (Opcode 64)
decompression and item deserialization for Equip and Prop bags.
"""

import socket
import time
import subprocess
import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(BASE_DIR, 'src'))
from ddt_protocol import (
    DDTPacket, DDTStreamWriter, DDTStreamReader,
    deserialize_grid_goods, HEADER_SIZE
)

TEST_PORT = 9205

def main():
    print(f"[*] Starting DDTank Server on test port {TEST_PORT}...")
    server_proc = subprocess.Popen(
        [sys.executable, os.path.join(BASE_DIR, 'src', 'ddt_server.py'), str(TEST_PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(1.2)

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5.0)
        s.connect(('127.0.0.1', TEST_PORT))
        print(f"[+] Connected to 127.0.0.1:{TEST_PORT}")

        # Step 1: Receive RSAKEY (Opcode 7)
        data = s.recv(1024)
        pkg_rsakey = DDTPacket.unpack(data)
        print(f"[+] Received packet: {pkg_rsakey}")
        assert pkg_rsakey.code == 7, f"Expected Opcode 7 (RSAKEY), got {pkg_rsakey.code}"

        # Step 2: Send LOGIN (Opcode 1)
        w = DDTStreamWriter()
        w.write_int(205) # Build version
        w.write_int(1)   # Desktop type
        w.write_utf("Admin")
        login_pkg = DDTPacket(code=1, client_id=1, payload=w.get_bytes())
        s.sendall(login_pkg.pack())
        print(f"[+] Sent LOGIN packet (Opcode 1)")

        # Step 3: Receive packets (LOGIN SelfInfo, SYS_DATE, BUFF_INFO, DAILY_AWARD, GRID_GOODS)
        received_packets = []
        buf = bytearray()
        start_time = time.time()

        while time.time() - start_time < 5.0:
            try:
                chunk = s.recv(4096)
                if not chunk:
                    break
                buf.extend(chunk)

                while len(buf) >= HEADER_SIZE:
                    try:
                        p = DDTPacket.unpack(bytes(buf))
                        total_len = HEADER_SIZE + len(p.payload)
                        received_packets.append(p)
                        buf = buf[total_len:]
                    except Exception:
                        break

                # We expect at least 6 packets: LOGIN (1), SYS_DATE (5), BUFF_INFO (0), DAILY_AWARD (13), GRID_GOODS (64, bag 0), GRID_GOODS (64, bag 1)
                opcodes = [p.code for p in received_packets]
                if 1 in opcodes and 64 in opcodes and opcodes.count(64) >= 2:
                    break
            except socket.timeout:
                break

        print(f"[+] Received {len(received_packets)} packets total:")
        for idx, p in enumerate(received_packets):
            print(f"  [{idx}] Opcode {p.code} (0x{p.code:04X}), len={len(p.payload)} bytes")

        # Step 4: Validate SelfInfo
        pkt_login = next((p for p in received_packets if p.code == 1), None)
        assert pkt_login is not None, "Missing LOGIN response packet!"
        assert len(pkt_login.payload) >= 400, f"LOGIN payload too short: {len(pkt_login.payload)} bytes"
        print(f"[+] SelfInfo Verified ({len(pkt_login.payload)} bytes)!")

        # Step 5: Validate GRID_GOODS (Opcode 64) for Equipment Bag (0) and Prop Bag (1)
        grid_packets = [p for p in received_packets if p.code == 64]
        assert len(grid_packets) >= 2, f"Expected 2 GRID_GOODS packets, got {len(grid_packets)}"

        # Bag 0 (Equip Bag)
        bag0, items0 = deserialize_grid_goods(grid_packets[0].payload, compressed=True)
        print(f"[+] GRID_GOODS Packet 1: BagType={bag0}, ItemCount={len(items0)}")
        assert bag0 == 0, f"Expected Bag 0, got {bag0}"
        assert len(items0) >= 20, f"Expected at least 20 equip items, got {len(items0)}"
        
        # Check Super Bumerangue +12
        weapon = next((it for it in items0 if it.get('template_id') == 7014), None)
        assert weapon is not None, "Super Bumerangue (7014) not found in Bag 0!"
        assert weapon['strengthen_level'] == 12
        assert weapon['is_gold'] is True
        print(f"  [+] Weapon in Place {weapon['place']}: Template {weapon['template_id']} (Level +{weapon['strengthen_level']}, Gold={weapon['is_gold']})")

        # Check Dom de Anjo
        offhand = next((it for it in items0 if it.get('template_id') == 17002), None)
        assert offhand is not None, "Dom de Anjo (17002) not found in Bag 0!"
        print(f"  [+] Offhand in Place {offhand['place']}: Template {offhand['template_id']} (Level +{offhand['strengthen_level']})")

        # Bag 1 (Prop Bag)
        bag1, items1 = deserialize_grid_goods(grid_packets[1].payload, compressed=True)
        print(f"[+] GRID_GOODS Packet 2: BagType={bag1}, ItemCount={len(items1)}")
        assert bag1 == 1, f"Expected Bag 1, got {bag1}"
        assert len(items1) >= 5, f"Expected at least 5 prop items, got {len(items1)}"
        stones = next((it for it in items1 if it.get('template_id') == 11023), None)
        assert stones is not None, "Strengthen Stones (11023) not found in Bag 1!"
        assert stones['count'] == 999
        print(f"  [+] Prop in Place {stones['place']}: Template {stones['template_id']} (Count={stones['count']})")

        print("==================================================================")
        print(" [SUCCESS] Phase 3 Inventory & VIP Arsenal 100% Smoke Verified!   ")
        print("==================================================================")

        s.close()

    finally:
        server_proc.terminate()
        try:
            server_proc.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            server_proc.kill()

if __name__ == '__main__':
    main()
