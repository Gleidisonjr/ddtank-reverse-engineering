"""
Automated Multi-Client Smoke Test for DDTank Lobby, Rooms & Chat (Phase 4)
Target: DDClássico (ddclassico.com) v2.0.5 / 7Road DDTank Engine
Simulates 2 concurrent players:
  - Player 1: Connects, logs in, creates a room, waits in slot 0 (Host).
  - Player 2: Connects, logs in, gets RoomList, joins Player 1's room in slot 1.
  - Player 2: Toggles READY state -> Player 1 receives state update.
  - Player 2: Chats "Bora jogar!" -> Player 1 receives message.
  - Player 1: Issues GM Command "/item 7004 1" -> receives system reply.
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
    deserialize_scene_chat, HEADER_SIZE
)

TEST_PORT = 9206

class TestClient:
    def __init__(self, username: str, port: int):
        self.username = username
        self.port = port
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.settimeout(4.0)
        self.client_id = 1
        self.buf = bytearray()

    def connect_and_login(self):
        self.s.connect(('127.0.0.1', self.port))
        # Receive RSAKEY (7)
        data = self.s.recv(1024)
        pkg = DDTPacket.unpack(data)
        assert pkg.code == 7, f"Expected Opcode 7, got {pkg.code}"

        # Send LOGIN (1)
        w = DDTStreamWriter()
        w.write_int(205)
        w.write_int(1)
        w.write_utf(self.username)
        self.s.sendall(DDTPacket(code=1, client_id=1, payload=w.get_bytes()).pack())

        # Read until SelfInfo & Inventory received
        packets = self.read_packets(expected_count=6)
        login_pkt = next((p for p in packets if p.code == 1), None)
        assert login_pkt is not None, "Missing LOGIN response"
        print(f"[+] [{self.username}] Authenticated and received SelfInfo ({len(login_pkt.payload)} bytes)")

    def send_packet(self, pkg: DDTPacket):
        self.s.sendall(pkg.pack())

    def read_packets(self, expected_count: int = 1, timeout: float = 3.0):
        received = []
        start = time.time()
        while time.time() - start < timeout:
            while len(self.buf) >= HEADER_SIZE:
                try:
                    p = DDTPacket.unpack(bytes(self.buf))
                    tot = HEADER_SIZE + len(p.payload)
                    received.append(p)
                    self.buf = self.buf[tot:]
                except Exception:
                    break
            if len(received) >= expected_count:
                break
            try:
                chunk = self.s.recv(4096)
                if not chunk: break
                self.buf.extend(chunk)
            except socket.timeout:
                break
        return received

    def close(self):
        self.s.close()


def main():
    print(f"[*] Starting DDTank Server on test port {TEST_PORT}...")
    server_proc = subprocess.Popen(
        [sys.executable, os.path.join(BASE_DIR, 'scripts', 'ddt_server.py'), str(TEST_PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(1.2)

    c1 = TestClient("Admin", TEST_PORT)
    c2 = TestClient("Gleidison", TEST_PORT)

    try:
        # Step 1: Connect and Login Player 1
        print("\n--- STEP 1: Player 1 (Admin) Login ---")
        c1.connect_and_login()

        # Step 2: Player 1 enters Hall (SCENE_LOGIN) and creates Room
        print("\n--- STEP 2: Player 1 Enters Hall & Creates Room ---")
        c1.send_packet(DDTPacket(code=16, client_id=1, payload=b'')) # SCENE_LOGIN
        pkts = c1.read_packets(expected_count=1)
        print(f"[+] Player 1 received initial RoomList (Opcode {pkts[0].code})")

        # Create Room (Opcode 94, subcode 0)
        w = DDTStreamWriter()
        w.write_byte(0) # subcode = GAME_ROOM_CREATE
        w.write_byte(0) # room_type = MATCH_ROOM
        w.write_byte(1) # time_type = 5s
        w.write_utf("Sala VIP Antigravity")
        w.write_utf("")
        c1.send_packet(DDTPacket(code=94, client_id=1, payload=w.get_bytes()))

        # Expect GAME_ROOM_CREATE & GAME_ROOM_ADDPLAYER
        room_pkts = c1.read_packets(expected_count=2)
        assert len(room_pkts) >= 2, f"Player 1 expected 2 room response packets, got {len(room_pkts)}"
        print(f"[+] Player 1 created Room! Received response opcodes: {[p.code for p in room_pkts]}")

        # Step 3: Connect and Login Player 2
        print("\n--- STEP 3: Player 2 (Gleidison) Login & Enters Hall ---")
        c2.connect_and_login()

        # Player 2 enters Hall and gets RoomList
        c2.send_packet(DDTPacket(code=16, client_id=2, payload=b''))
        c2_pkts = c2.read_packets(expected_count=1)
        assert c2_pkts[0].code == 94, "Expected Opcode 94 (GAME_ROOM) RoomList"

        # Inspect RoomList payload
        r_list = DDTStreamReader(c2_pkts[0].payload)
        sub = r_list.read_ubyte()
        assert sub == 9, f"Expected subcode 9 (ROOMLIST_UPDATE), got {sub}"
        total_rooms = r_list.read_int()
        count = r_list.read_int()
        print(f"[+] Player 2 received RoomList: TotalRooms={total_rooms}, ActiveRooms={count}")
        assert count >= 1, "Player 1's room should appear in RoomList!"
        room_id = r_list.read_int()
        room_type = r_list.read_byte()
        time_type = r_list.read_byte()
        total_p = r_list.read_byte()
        view_cnt = r_list.read_byte()
        max_v = r_list.read_byte()
        plc_cnt = r_list.read_byte()
        is_lck = r_list.read_boolean()
        map_id = r_list.read_int()
        is_play = r_list.read_boolean()
        room_name = r_list.read_utf()
        print(f"  [+] Found Room #{room_id}: '{room_name}' (Slots: {plc_cnt}, Mode: {room_type})")
        assert room_name == "Sala VIP Antigravity"

        # Step 4: Player 2 joins Room #1
        print("\n--- STEP 4: Player 2 Joins Room #1 ---")
        w_join = DDTStreamWriter()
        w_join.write_byte(1) # subcode = GAME_ROOM_LOGIN
        w_join.write_int(room_id)
        c2.send_packet(DDTPacket(code=94, client_id=2, payload=w_join.get_bytes()))

        # Player 2 reads room sync packets
        join_pkts = c2.read_packets(expected_count=3)
        print(f"[+] Player 2 joined successfully! Received {len(join_pkts)} room synchronization packets")

        # Player 1 should receive GAME_ROOM_ADDPLAYER for Player 2
        p1_pkts = c1.read_packets(expected_count=1)
        assert len(p1_pkts) >= 1, "Player 1 should receive Player 2 join notice!"
        print(f"[+] Player 1 received Player 2 Join Notification (Opcode {p1_pkts[0].code})")

        # Step 5: Player 2 toggles READY state
        print("\n--- STEP 5: Player 2 Toggles Ready State ---")
        w_ready = DDTStreamWriter()
        w_ready.write_byte(15) # subcode = GAME_PLAYER_STATE_CHANGE
        w_ready.write_byte(1)  # state = 1 (Ready)
        c2.send_packet(DDTPacket(code=94, client_id=2, payload=w_ready.get_bytes()))

        # Player 1 receives state update
        state_pkts = c1.read_packets(expected_count=1)
        assert len(state_pkts) >= 1
        r_state = DDTStreamReader(state_pkts[0].payload)
        assert r_state.read_ubyte() == 15, "Expected subcode 15"
        slot0_state = r_state.read_ubyte() # Host (2)
        slot1_state = r_state.read_ubyte() # Ready (1)
        print(f"[+] Player 1 verified Player 2 State Update: Slot 0 = {slot0_state} (Host), Slot 1 = {slot1_state} (Ready)")
        assert slot1_state == 1

        # Step 6: Real-time In-Room Chat Exchange
        print("\n--- STEP 6: Real-Time In-Room Chat Exchange ---")
        w_chat = DDTStreamWriter()
        w_chat.write_int(1)     # zoneID
        w_chat.write_byte(0)    # channel
        w_chat.write_boolean(False) # is_team
        w_chat.write_utf("Gleidison")
        w_chat.write_utf("Bora jogar, pronto pro tiro certeiro!")
        c2.send_packet(DDTPacket(code=19, client_id=2, payload=w_chat.get_bytes()))

        chat_pkts = c1.read_packets(expected_count=1)
        assert len(chat_pkts) >= 1
        assert chat_pkts[0].code == 19
        c_data = deserialize_scene_chat(chat_pkts[0].payload)
        print(f"[+] Player 1 received chat message from '{c_data['sender']}': '{c_data['msg']}'")
        assert "Bora jogar" in c_data['msg']

        # Step 7: GM Command Execution via Chat
        print("\n--- STEP 7: GM Command Execution via Chat ---")
        w_gm = DDTStreamWriter()
        w_gm.write_int(1)
        w_gm.write_byte(0)
        w_gm.write_boolean(False)
        w_gm.write_utf("Admin")
        w_gm.write_utf("/item 7004 1") # Give Super Quebra-Tijolos
        c1.send_packet(DDTPacket(code=19, client_id=1, payload=w_gm.get_bytes()))

        # Expect system chat reply + GRID_GOODS packet update
        gm_pkts = c1.read_packets(expected_count=2)
        sys_chat = next((p for p in gm_pkts if p.code == 19), None)
        assert sys_chat is not None, "Missing GM system reply chat packet"
        sys_data = deserialize_scene_chat(sys_chat.payload)
        print(f"[+] GM System Reply: [{sys_data['sender']}]: {sys_data['msg']}")
        assert "adicionado" in sys_data['msg']

        print("==================================================================")
        print(" [SUCCESS] Phase 4 Lobby, Rooms & Multi-Client 100% Smoke Verified! ")
        print("==================================================================")

    finally:
        c1.close()
        c2.close()
        server_proc.terminate()
        try:
            server_proc.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            server_proc.kill()

if __name__ == '__main__':
    main()
