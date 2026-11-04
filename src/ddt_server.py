"""
DDTank Core Emulation Server (Center & Login Gateway)
Target: DDClássico (ddclassico.com) v2.0.5 / 7Road DDTank Engine
Handles TCP sockets on port 9200, RSA handshake, Login, SelfInfo serialization,
Heartbeats, and SQLite account persistence.
"""

import asyncio
import sqlite3
import os
import sys
import struct
import datetime
from typing import Dict

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.dirname(__file__))
sys.path.append(BASE_DIR)
from ddt_protocol import (
    DDTPacket, DDTStreamCipher, DDTStreamWriter, DDTStreamReader,
    serialize_grid_goods, deserialize_grid_goods,
    serialize_scene_chat, deserialize_scene_chat,
    serialize_room_list, serialize_room_create,
    serialize_room_add_player, serialize_room_player_state,
    HEADER_SIZE, DEFAULT_KEY
)

PORT = 9200
DB_PATH = os.path.join(BASE_DIR, 'data', 'ddtank.db')

POLICY_XML = (
    b'<?xml version="1.0"?>\n'
    b'<!DOCTYPE cross-domain-policy SYSTEM "http://www.adobe.com/xml/dtds/cross-domain-policy.dtd">\n'
    b'<cross-domain-policy>\n'
    b'    <allow-access-from domain="*" to-ports="*" />\n'
    b'    <site-control permitted-cross-domain-policies="all" />\n'
    b'</cross-domain-policy>\x00'
)


def init_database():
    """Initializes SQLite database with default Admin and test accounts."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            nickname TEXT,
            grade INTEGER DEFAULT 60,
            gold INTEGER DEFAULT 9999999,
            money INTEGER DEFAULT 9999999,
            attack INTEGER DEFAULT 1250,
            defence INTEGER DEFAULT 1100,
            agility INTEGER DEFAULT 950,
            luck INTEGER DEFAULT 1050,
            damage INTEGER DEFAULT 800,
            armor INTEGER DEFAULT 500,
            vip_level INTEGER DEFAULT 12,
            fight_power INTEGER DEFAULT 450000,
            sex INTEGER DEFAULT 1,
            style TEXT DEFAULT '1142,2101,3105,4101,5101,6101,7014,9002,9002,9022,9022,13101,14001,15001,16001,17002',
            colors TEXT DEFAULT ',,,,,,,,,,,,,,,',
            skin TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("SELECT id FROM users WHERE username = 'Admin'")
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO users (username, nickname, grade, gold, money, style, colors)
            VALUES ('Admin', 'GM_Dopamine', 65, 9999999, 9999999,
                    '1142,2101,3105,4101,5101,6101,7014,9002,9002,9022,9022,13101,14001,15001,16001,17002',
                    ',,,,,,,,,,,,,,,')
        """)
    else:
        cur.execute("""
            UPDATE users SET 
                style = '1142,2101,3105,4101,5101,6101,7014,9002,9002,9022,9022,13101,14001,15001,16001,17002',
                colors = ',,,,,,,,,,,,,,,'
            WHERE username = 'Admin'
        """)
    conn.commit()
    conn.close()
    print(f"[+] Initialized DDTank SQLite Database at {DB_PATH}")


def get_or_create_user(username: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    if not row:
        cur.execute("""
            INSERT INTO users (username, nickname, grade, gold, money)
            VALUES (?, ?, 60, 5000000, 5000000)
        """, (username, username))
        conn.commit()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
    user_dict = dict(row)
    conn.close()
    return user_dict


class DDTClientSession:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, server):
        self.reader = reader
        self.writer = writer
        self.server = server
        self.addr = writer.get_extra_info('peername')
        self.cipher_in = DDTStreamCipher()
        self.cipher_out = DDTStreamCipher()
        self.encrypted = False
        self.user = None
        self.client_id = 1
        self.running = True
        self.in_lobby = False
        self.current_room = None
        self.room_place = -1

    async def run(self):
        print(f"[+] Client connected from {self.addr[0]}:{self.addr[1]}")
        self.server.register_session(self)
        try:
            # Brief peek for inline Flash Socket Policy (<policy-file-request/>) before sending binary RSAKEY
            first_data = None
            try:
                first_data = await asyncio.wait_for(self.reader.read(4096), timeout=0.15)
                if not first_data:
                    return
                if b'<policy-file-request/>' in first_data or b'policy' in first_data.lower():
                    print(f"[+] Served inline Flash socket policy to {self.addr[0]}")
                    self.writer.write(POLICY_XML)
                    await self.writer.drain()
                    return
            except asyncio.TimeoutError:
                first_data = None

            # Game socket connection: send RSAKEY (Opcode 7) immediately
            await self.send_rsakey()

            if first_data:
                await self.handle_raw_data(first_data)

            # Main read loop
            while self.running:
                data = await self.reader.read(4096)
                if not data:
                    break

                if b'<policy-file-request/>' in data or b'policy' in data.lower():
                    print(f"[+] Served inline Flash socket policy to {self.addr[0]}")
                    self.writer.write(POLICY_XML)
                    await self.writer.drain()
                    continue

                await self.handle_raw_data(data)

        except ConnectionResetError:
            pass
        except Exception as e:
            print(f"[-] Session error for {self.addr[0]}: {e}")
        finally:
            print(f"[*] Client disconnected from {self.addr[0]}:{self.addr[1]}")
            self.running = False
            self.server.unregister_session(self)
            self.writer.close()

    async def handle_raw_data(self, raw_data: bytes):
        if self.encrypted:
            plain_data = self.cipher_in.decrypt(raw_data)
        else:
            plain_data = raw_data

        pos = 0
        while pos + HEADER_SIZE <= len(plain_data):
            try:
                pkg = DDTPacket.unpack(plain_data[pos:])
                total_len = HEADER_SIZE + len(pkg.payload)
                pos += total_len
                await self.process_packet(pkg)
            except Exception as e:
                # Advance 1 byte on sync loss
                pos += 1

    async def process_packet(self, pkg: DDTPacket):
        code = pkg.code
        # ePackageType.LOGIN = 1
        if code == 1:
            await self.handle_login(pkg)
        # ePackageType.PING = 4
        elif code == 4:
            await self.handle_ping(pkg)
        # ePackageType.SCENE_LOGIN = 16
        elif code == 16:
            await self.handle_scene_login(pkg)
        # ePackageType.SCENE_CHAT = 19
        elif code == 19:
            await self.handle_scene_chat(pkg)
        # ePackageType.GAME_ROOM = 94
        elif code == 94:
            await self.handle_game_room(pkg)
        else:
            print(f"[*] Received unhandled Opcode {code} (0x{code:04X}) from {self.addr[0]} (len={len(pkg.payload)})")

    async def send_rsakey(self):
        """Sends RSAKEY (Opcode 7) to initialize crypto handshake."""
        w = DDTStreamWriter()
        # Modulus & Exponent
        w.write_bytes(bytes([0x01] * 8))
        pkg = DDTPacket(code=7, client_id=self.client_id, payload=w.get_bytes())
        await self.send_packet(pkg)
        print(f"[+] Sent RSAKEY (0x07) to {self.addr[0]}")

    async def handle_login(self, pkg: DDTPacket):
        """Processes player LOGIN packet (Opcode 1)."""
        r = DDTStreamReader(pkg.payload)
        build_ver = r.read_int()
        desktop_type = r.read_int()
        print(f"[+] Received LOGIN packet: Build {build_ver}, Desktop {desktop_type}")

        # The rest is encrypted byte array or direct payload
        username = "Admin"
        if r.bytes_available > 0:
            try:
                cand = r.read_utf()
                if cand:
                    username = cand
            except Exception:
                pass
        self.user = get_or_create_user(username)
        self.client_id = self.user['id']
        print(f"[+] Authenticated user ID {self.client_id} '{self.user['username']}' (Nick: '{self.user['nickname']}', Level {self.user['grade']})")

        # Now send the authoritative LOGIN response (Opcode 1)
        await self.send_login_response()

        # Send SYS_DATE (Opcode 5)
        await self.send_sys_date()

        # Send BUFF_INFO (Opcode 0)
        await self.send_buff_info()

        # Send DAILY_AWARD (Opcode 13)
        await self.send_daily_award()

        # Send Authoritative Inventory & VIP Arsenal (Opcode 64: GRID_GOODS)
        await self.send_inventory()

        print(f"[+] Login sequence completed for {self.user['nickname']}. Transitioning to Lobby!")

    async def send_login_response(self):
        """Serializes full SelfInfo in LOGIN packet response."""
        u = self.user
        w = DDTStreamWriter()
        
        # 1. Result byte (0 = Success)
        w.write_byte(0)
        
        # 2. ZoneID & Combat Stats
        w.write_int(1)          # ZoneID
        w.write_int(u['attack']) # Attack
        w.write_int(u['defence'])# Defence
        w.write_int(u['agility'])# Agility
        w.write_int(u['luck'])   # Luck
        w.write_int(u['damage']) # cDamage
        w.write_int(u['armor'])  # cArmor
        
        # 3. GP (Exp), Repute, Currencies
        w.write_long(9500000)    # GP / EXP (Level 60+)
        w.write_int(50000)       # Repute
        w.write_int(u['gold'])   # Gold
        w.write_int(u['money'])  # Money (Cash)
        w.write_int(0)           # MoneyLock
        w.write_int(5000)        # medal
        w.write_int(10000)       # Score
        w.write_int(0)           # Hide
        w.write_long(u['fight_power']) # FightPower
        
        # 4. Master / Apprenticeship
        w.write_int(0)           # apprenticeshipState
        w.write_int(0)           # masterID
        w.write_utf("")          # masterName
        w.write_int(0)           # graduatesCount
        w.write_utf("")          # honourOfMaster
        
        # 5. Freezes & VIP System
        now = datetime.datetime.now()
        w.write_bytes(self._serialize_date(now)) # freezesDate
        w.write_byte(1)          # typeVIP
        w.write_int(u['vip_level']) # VIPLevel (12)
        w.write_int(999999)      # VIPExp
        w.write_bytes(self._serialize_date(now + datetime.timedelta(days=365))) # VIPExpireDay
        w.write_bytes(self._serialize_date(now)) # LastDate
        w.write_int(0)           # VIPNextLevelDaysNeeded
        w.write_bytes(self._serialize_date(now)) # systemDate
        w.write_boolean(True)    # canTakeVipReward
        w.write_int(1)           # OptionOnOff
        w.write_int(2500)        # AchievementPoint
        w.write_utf("Lenda do DDTank") # honor
        w.write_int(36000)       # totalGameTime
        
        # 6. Character Style & Visuals
        w.write_boolean(bool(u['sex'])) # Sex (True = Male)
        w.write_utf(u['style'])  # Style (Equipped item IDs)
        w.write_utf(u['colors']) # Colors
        w.write_utf(u['skin'])   # Skin
        
        # 7. Consortia / Guild System
        w.write_int(101)         # ConsortiaID
        w.write_utf("DDClássico VIP") # ConsortiaName
        w.write_int(1)           # badgeID
        w.write_int(1)           # DutyLevel
        w.write_utf("Líder")     # DutyName
        w.write_int(0xFFFFFF)    # Right
        w.write_utf(u['nickname']) # ChairmanName
        w.write_int(10000)       # Honor
        w.write_int(50000)       # Riches
        
        # 8. Bag Lock / Security
        w.write_boolean(False)   # bagPwdState
        w.write_utf("")          # questionOne
        w.write_utf("")          # questionTwo
        w.write_int(3)           # leftTimes
        
        # 9. Miscellaneous & TEXP System
        w.write_utf(u['username']) # LoginName
        w.write_int(1)           # Nimbus
        w.write_utf("1111111111") # PvePermission
        w.write_utf("")          # fightLibMission
        w.write_int(0)           # userGuildProgress
        w.write_int(1)           # receiebox
        w.write_int(u['grade'])  # receieGrade
        w.write_int(0)           # needGetBoxTime
        w.write_bytes(self._serialize_date(now)) # LastSpaDate
        w.write_bytes(self._serialize_date(now)) # shopFinallyGottenTime
        w.write_int(0)           # UseOffer
        w.write_int(100)         # dailyScore
        w.write_int(10)          # dailyWinCount
        w.write_int(12)          # dailyGameCount
        w.write_boolean(True)    # DailyLeagueFirst
        w.write_int(1500)        # DailyLeagueLastScore
        w.write_int(500)         # weeklyScore
        w.write_int(20)          # weeklyGameCount
        w.write_int(1)           # weeklyRanking
        
        # TEXP Stats
        w.write_int(500)         # spdTexpExp
        w.write_int(500)         # attTexpExp
        w.write_int(500)         # defTexpExp
        w.write_int(500)         # hpTexpExp
        w.write_int(500)         # lukTexpExp
        w.write_int(5)           # texpTaskCount
        w.write_int(10)          # texpCount
        w.write_bytes(self._serialize_date(now)) # texpTaskDate
        w.write_boolean(True)    # isOldPlayerHasValidEquitAtLogin
        w.write_int(0)           # badLuckNumber
        w.write_int(7)           # luckyNum
        w.write_bytes(self._serialize_date(now)) # lastLuckyNumDate
        w.write_int(7)           # lastLuckNum
        w.write_int(10)          # totemId
        w.write_int(30)          # accumulativeLoginDays
        w.write_int(30)          # accumulativeAwardDays
        w.write_boolean(False)   # isOld
        w.write_utf("Desktop")   # clientInstance

        pkg = DDTPacket(code=1, client_id=self.client_id, payload=w.get_bytes())
        await self.send_packet(pkg)
        print(f"[+] Dispatched SelfInfo payload ({len(pkg.payload)} bytes) in LOGIN packet response!")

    async def send_sys_date(self):
        """Sends SYS_DATE (Opcode 5)."""
        w = DDTStreamWriter()
        w.write_bytes(self._serialize_date(datetime.datetime.now()))
        pkg = DDTPacket(code=5, client_id=self.client_id, payload=w.get_bytes())
        await self.send_packet(pkg)

    async def send_buff_info(self):
        """Sends BUFF_INFO (Opcode 0)."""
        w = DDTStreamWriter()
        w.write_int(0) # Buff count
        pkg = DDTPacket(code=0, client_id=self.client_id, payload=w.get_bytes())
        await self.send_packet(pkg)

    async def send_daily_award(self):
        """Sends DAILY_AWARD (Opcode 13)."""
        w = DDTStreamWriter()
        w.write_int(0)
        pkg = DDTPacket(code=13, client_id=self.client_id, payload=w.get_bytes())
        await self.send_packet(pkg)

    async def send_inventory(self):
        """Fetches player inventory from SQLite and sends GRID_GOODS (Opcode 64) for bags 0 & 1."""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM items WHERE user_id = ? ORDER BY place ASC", (self.user['id'],))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()

        equip_items = [r for r in rows if r['bag_type'] == 0]
        prop_items = [r for r in rows if r['bag_type'] == 1]

        if equip_items:
            pkt_equip = serialize_grid_goods(bag_type=0, items=equip_items, compress=True)
            pkt_equip.client_id = self.client_id
            await self.send_packet(pkt_equip)
            print(f"[+] Sent GRID_GOODS (Bag 0 - Equip): {len(equip_items)} items to {self.addr[0]}")

        if prop_items:
            pkt_prop = serialize_grid_goods(bag_type=1, items=prop_items, compress=True)
            pkt_prop.client_id = self.client_id
            await self.send_packet(pkt_prop)
            print(f"[+] Sent GRID_GOODS (Bag 1 - Prop): {len(prop_items)} items to {self.addr[0]}")

    async def handle_ping(self, pkg: DDTPacket):
        """Responds to PING (Opcode 4) keepalive."""
        resp = DDTPacket(code=4, client_id=self.client_id, payload=pkg.payload)
        await self.send_packet(resp)

    async def handle_scene_login(self, pkg: DDTPacket):
        """Handles player entering Hall/Lobby Scene (Opcode 16)."""
        self.in_lobby = True
        print(f"[+] Player {self.user['nickname']} entered Lobby / Scene!")
        # Send room list to player entering the hall
        pkt_list = serialize_room_list(list(self.server.rooms.values()))
        await self.send_packet(pkt_list)

    async def handle_scene_chat(self, pkg: DDTPacket):
        """Handles player chat messages and GM commands (Opcode 19)."""
        chat_data = deserialize_scene_chat(pkg.payload, client_id=self.client_id)
        msg = chat_data['msg'].strip()
        sender_name = self.user['nickname']
        print(f"[*] Chat [{chat_data['channel']}] {sender_name}: {msg}")

        # Intercept GM Commands starting with '/'
        if msg.startswith('/'):
            await self.handle_gm_command(msg)
            return

        # Broadcast standard chat message
        out_pkg = serialize_scene_chat(
            zone_id=1,
            channel=chat_data['channel'],
            sender=sender_name,
            msg=msg,
            sender_id=self.client_id
        )
        if getattr(self, 'current_room', None):
            await self.server.broadcast_room(self.current_room, out_pkg)
        else:
            await self.server.broadcast_lobby(out_pkg)

    async def handle_gm_command(self, cmd_str: str):
        """Executes server authoritative GM commands typed into in-game chat."""
        parts = cmd_str.split()
        cmd = parts[0].lower()
        args = parts[1:]

        async def reply_sys(text: str):
            pkt = serialize_scene_chat(zone_id=1, channel=0, sender="[GM Sistema]", msg=text, sender_id=999)
            await self.send_packet(pkt)

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        if cmd == '/help':
            await reply_sys("Comandos GM: /gold <qtd>, /money <qtd>, /level <nv>, /item <template_id> [qtd]")
        elif cmd == '/gold' and args:
            qty = int(args[0])
            cur.execute("UPDATE users SET gold = gold + ? WHERE id = ?", (qty, self.user['id']))
            conn.commit()
            await reply_sys(f"[+] Ouro adicionado: +{qty:,}!")
        elif cmd == '/money' and args:
            qty = int(args[0])
            cur.execute("UPDATE users SET money = money + ? WHERE id = ?", (qty, self.user['id']))
            conn.commit()
            await reply_sys(f"[+] Moedas (Cash) adicionadas: +{qty:,}!")
        elif cmd == '/level' and args:
            lvl = max(1, min(65, int(args[0])))
            cur.execute("UPDATE users SET grade = ? WHERE id = ?", (lvl, self.user['id']))
            conn.commit()
            await reply_sys(f"[+] Nivel alterado para {lvl}!")
        elif cmd == '/item' and args:
            tid = int(args[0])
            count = int(args[1]) if len(args) > 1 else 1
            cur.execute("SELECT MAX(place) FROM items WHERE user_id = ? AND bag_type = 0", (self.user['id'],))
            row = cur.fetchone()
            max_p = row[0] if row and row[0] is not None else 30
            new_p = max_p + 1
            cur.execute("""
                INSERT INTO items (user_id, item_id, template_id, bag_type, place, count, strengthen_level, is_bind)
                VALUES (?, ?, ?, 0, ?, ?, 12, 1)
            """, (self.user['id'], 3000 + new_p, tid, new_p, count))
            conn.commit()
            await reply_sys(f"[+] Item {tid} (x{count}) adicionado no slot {new_p}!")
            await self.send_inventory()
        else:
            await reply_sys(f"[-] Comando desconhecido '{cmd}'. Digite /help para ver os comandos.")
        conn.close()

    async def handle_game_room(self, pkg: DDTPacket):
        """Dispatches subcodes of ePackageType.GAME_ROOM (Opcode 94)."""
        r = DDTStreamReader(pkg.payload)
        sub_code = r.read_ubyte()

        # Subcode 0: GAME_ROOM_CREATE
        if sub_code == 0:
            room_type = r.read_byte() if r.bytes_available else 0
            time_type = r.read_byte() if r.bytes_available else 1
            room_name = r.read_utf() if r.bytes_available else f"Sala de {self.user['nickname']}"
            pwd = r.read_utf() if r.bytes_available else ""

            room = self.server.create_room(self, name=room_name, room_type=room_type, time_type=time_type)
            print(f"[+] Created Room #{room['id']}: '{room['name']}' by {self.user['nickname']}")

            # Send GAME_ROOM_CREATE response to host
            pkt_create = serialize_room_create(room)
            await self.send_packet(pkt_create)

            # Send GAME_ROOM_ADDPLAYER for host
            pkt_add = serialize_room_add_player(self.user, is_first_in=True, place=0, team=1, is_host=True)
            await self.send_packet(pkt_add)

            # Broadcast updated room list to all lobby players
            await self.server.broadcast_lobby(serialize_room_list(list(self.server.rooms.values())))

        # Subcode 1: GAME_ROOM_LOGIN (Enter room)
        elif sub_code == 1:
            room_id = r.read_int()
            res = self.server.join_room(self, room_id)
            if res:
                room, place = res
                print(f"[+] Player {self.user['nickname']} joined Room #{room_id} at place {place}")
                # Send GAME_ROOM_CREATE to new player
                await self.send_packet(serialize_room_create(room))

                # Send GAME_ROOM_ADDPLAYER for all players currently in room to the new player
                for s in room['players']:
                    is_h = (s == room['host'])
                    p_place = s.room_place
                    team = room['teams'][p_place]
                    await self.send_packet(serialize_room_add_player(s.user, is_first_in=(s == self), place=p_place, team=team, is_host=is_h))

                # Broadcast GAME_ROOM_ADDPLAYER for new player to other room players
                pkt_new = serialize_room_add_player(self.user, is_first_in=False, place=place, team=room['teams'][place], is_host=False)
                await self.server.broadcast_room(room_id, pkt_new, exclude=self)

                # Broadcast state changes
                await self.server.broadcast_room(room_id, serialize_room_player_state(room['states']))

        # Subcode 9: ROOMLIST_UPDATE
        elif sub_code == 9:
            pkt_list = serialize_room_list(list(self.server.rooms.values()))
            await self.send_packet(pkt_list)

        # Subcode 15: GAME_PLAYER_STATE_CHANGE (Toggle Ready / Cancel)
        elif sub_code == 15:
            state = r.read_byte() if r.bytes_available else 1
            rid = getattr(self, 'current_room', None)
            if rid and rid in self.server.rooms:
                room = self.server.rooms[rid]
                place = getattr(self, 'room_place', 0)
                room['states'][place] = state
                print(f"[+] Player {self.user['nickname']} toggled state to {state} in room #{rid}")
                await self.server.broadcast_room(rid, serialize_room_player_state(room['states']))

    async def send_packet(self, pkg: DDTPacket):
        raw = pkg.pack()
        if self.encrypted:
            enc = self.cipher_out.encrypt(raw)
        else:
            enc = raw
        self.writer.write(enc)
        await self.writer.drain()

    def _serialize_date(self, dt: datetime.datetime) -> bytes:
        """Serializes ActionScript 3 Date primitive (Year, Month, Date, Hour, Min, Sec)."""
        return struct.pack('>HBBBBB', dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)


class DDTSocketServer:
    def __init__(self, host: str = "0.0.0.0", port: int = PORT):
        self.host = host
        self.port = port
        self.server = None
        self.sessions = []
        self.rooms = {}
        self.next_room_id = 1

    def register_session(self, session):
        self.sessions.append(session)

    def unregister_session(self, session):
        if session in self.sessions:
            self.sessions.remove(session)
        self.leave_room(session)

    async def broadcast_lobby(self, pkg: DDTPacket, exclude=None):
        for s in list(self.sessions):
            if s != exclude and s.running and getattr(s, 'in_lobby', False):
                try:
                    await s.send_packet(pkg)
                except Exception:
                    pass

    async def broadcast_room(self, room_id: int, pkg: DDTPacket, exclude=None):
        room = self.rooms.get(room_id)
        if not room: return
        for s in list(room['players']):
            if s != exclude and s.running:
                try:
                    await s.send_packet(pkg)
                except Exception:
                    pass

    def create_room(self, host_session, name="Sala de Jogo", room_type=0, time_type=1, map_id=1, is_locked=False):
        rid = self.next_room_id
        self.next_room_id += 1
        room = {
            'id': rid,
            'name': name,
            'type': room_type,
            'time_type': time_type,
            'map_id': map_id,
            'total_player': 2,
            'viewer_cnt': 0,
            'max_viewer_cnt': 2,
            'place_count': 4,
            'is_locked': is_locked,
            'started': False,
            'is_playing': False,
            'game_mode': 0,
            'hard_level': 0,
            'level_limits': 0,
            'host': host_session,
            'players': [host_session],
            'slots': [host_session, None, None, None],
            'teams': [1, 2, 1, 2],
            'states': [2, 0, 0, 0] # 2 = Host, 1 = Ready, 0 = Empty/Not Ready
        }
        self.rooms[rid] = room
        host_session.current_room = rid
        host_session.room_place = 0
        return room

    def join_room(self, session, room_id: int):
        room = self.rooms.get(room_id)
        if not room: return None
        for i in range(len(room['slots'])):
            if room['slots'][i] is None:
                room['slots'][i] = session
                room['players'].append(session)
                room['states'][i] = 0 # Not Ready
                session.current_room = room_id
                session.room_place = i
                room['total_player'] = len(room['players'])
                return room, i
        return None

    def leave_room(self, session):
        rid = getattr(session, 'current_room', None)
        if not rid or rid not in self.rooms: return
        room = self.rooms[rid]
        if session in room['players']:
            room['players'].remove(session)
        place = getattr(session, 'room_place', -1)
        if 0 <= place < len(room['slots']):
            room['slots'][place] = None
            room['states'][place] = 0
        session.current_room = None
        session.room_place = -1
        room['total_player'] = len(room['players'])

        if not room['players']:
            del self.rooms[rid]
            print(f"[*] Destroyed empty Room #{rid}")
        elif room['host'] == session:
            new_host = room['players'][0]
            room['host'] = new_host
            new_place = room['slots'].index(new_host)
            room['states'][new_place] = 2 # Promote to Host
            print(f"[*] Transferred host of Room #{rid} to {new_host.user['nickname']}")

    async def start(self):
        init_database()
        self._release_stale_python_listener()
        try:
            self.server = await asyncio.start_server(
                lambda r, w: DDTClientSession(r, w, self).run(),
                self.host, self.port
            )
        except OSError as e:
            print(f"[-] Porta TCP {self.port} ocupada ({e}). Verifique se outro serviço está usando a porta {self.port}.")
            raise
        print("==================================================================")
        print(f"       DDTank Game Core Socket Server Listening on {self.port}       ")
        print("==================================================================")
        async with self.server:
            await self.server.serve_forever()

    def _release_stale_python_listener(self):
        if sys.platform != 'win32':
            return
        import subprocess, time
        my_pid = os.getpid()
        try:
            out = subprocess.check_output(['netstat', '-ano', '-p', 'tcp'], stderr=subprocess.DEVNULL).decode('latin1', errors='ignore')
        except Exception:
            return
        pids = set()
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 5 and parts[0].upper() == 'TCP':
                if parts[1].endswith(f':{self.port}') and parts[2].endswith(':0'):
                    try:
                        pid = int(parts[-1])
                        if pid > 4 and pid != my_pid:
                            pids.add(pid)
                    except ValueError:
                        pass
        for pid in pids:
            try:
                cmd_out = subprocess.check_output(
                    [
                        'powershell', '-NoProfile', '-Command',
                        f"(Get-CimInstance Win32_Process -Filter 'ProcessId={pid}').CommandLine"
                    ],
                    stderr=subprocess.DEVNULL
                ).decode('utf-8', errors='ignore').strip().lower()
                if 'ddt_' in cmd_out:
                    print(f"[*] Encerrando instância anterior do ddt_server (PID {pid}) na porta {self.port}...")
                    subprocess.run(['taskkill', '/F', '/PID', str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    time.sleep(0.4)
            except Exception:
                pass


if __name__ == '__main__':
    p = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    try:
        asyncio.run(DDTSocketServer(port=p).start())
    except KeyboardInterrupt:
        print("\n[*] Game Server shut down.")
