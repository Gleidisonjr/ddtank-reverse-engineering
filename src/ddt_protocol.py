"""
DDTank Master Protocol & Network Serializer/Cipher
Target: DDClássico (ddclassico.com) v2.0.5 / 7Road DDTank Engine
Extracted directly from Flash ActionScript 3 Bytecode (2.swf DoABC tags:
  road7th.comm.ByteSocket, road7th.comm.PackageIn, road7th.comm.PackageOut,
  ddt.data.socket.ePackageType, ddt.data.socket.CrazyTankPackageType).
"""

import struct
import zlib
from typing import Tuple, List, Optional, Union, Dict, Any

# Protocol Header Constants
HEADER_MAGIC = 0x71AB  # 29099
HEADER_SIZE = 20
DEFAULT_KEY = [0xAE, 0xBF, 0x56, 0x78, 0xAB, 0xCD, 0xEF, 0xF1]


class DDTStreamCipher:
    """
    Symmetric stateful rolling byte cipher used by 7Road ByteSocket.
    Dynamic key mutation occurs at every byte offset based on previous ciphertext.
    """
    def __init__(self, key: Optional[List[int]] = None):
        self.key = list(key if key is not None else DEFAULT_KEY)

    def reset(self, key: Optional[List[int]] = None):
        self.key = list(key if key is not None else DEFAULT_KEY)

    def encrypt(self, data: bytes) -> bytes:
        """
        Encrypts plaintext packet bytes using the stateful rolling key.
        Matches ByteSocket::send.
        """
        res = bytearray(len(data))
        prev_cipher = 0
        for i in range(len(data)):
            b_plain = data[i]
            if i > 0:
                k_idx = i % 8
                self.key[k_idx] = ((self.key[k_idx] + prev_cipher) & 0xFF) ^ i
                b_cipher = ((b_plain ^ self.key[k_idx]) + prev_cipher) & 0xFF
            else:
                b_cipher = b_plain ^ self.key[0]
            prev_cipher = b_cipher
            res[i] = b_cipher
        return bytes(res)

    def decrypt(self, data: bytes) -> bytes:
        """
        Decrypts ciphertext packet bytes using the stateful rolling key.
        Matches PackageIn::loadE.
        """
        res = bytearray(len(data))
        prev_cipher = 0
        for i in range(len(data)):
            b_cipher = data[i]
            if i > 0:
                k_idx = i % 8
                self.key[k_idx] = ((self.key[k_idx] + prev_cipher) & 0xFF) ^ i
                b_plain = ((b_cipher - prev_cipher) & 0xFF) ^ self.key[k_idx]
            else:
                b_plain = b_cipher ^ self.key[0]
            prev_cipher = b_cipher
            res[i] = b_plain
        return bytes(res)


def calculate_checksum(buffer: bytes) -> int:
    """
    Calculates DDTank packet checksum.
    Matches PackageOut::calculateCheckSum & PackageIn::calculateCheckSum:
      sum = 119
      for byte in buffer[6:]: sum += byte
      return sum & 0x7F7F (32639)
    """
    chk = 119
    for b in buffer[6:]:
        chk += b
    return chk & 0x7F7F


class DDTStreamWriter:
    """Helper to serialize ActionScript 3 ByteArray primitives (Big-Endian)."""
    def __init__(self):
        self.buffer = bytearray()

    def write_byte(self, val: int):
        self.buffer.append(val & 0xFF)

    def write_boolean(self, val: bool):
        self.write_byte(1 if val else 0)

    def write_short(self, val: int):
        self.buffer.extend(struct.pack('>h', val))

    def write_ushort(self, val: int):
        self.buffer.extend(struct.pack('>H', val))

    def write_int(self, val: int):
        self.buffer.extend(struct.pack('>i', val))

    def write_uint(self, val: int):
        self.buffer.extend(struct.pack('>I', val))

    def write_long(self, val: int):
        self.buffer.extend(struct.pack('>q', val))

    def write_utf(self, s: str):
        encoded = s.encode('utf-8')
        self.write_ushort(len(encoded))
        self.buffer.extend(encoded)

    def write_date_string(self, year: int = 2026, month: int = 11, day: int = 3, hour: int = 12, minute: int = 0, second: int = 0):
        """Serializes 7-byte date string format: Short(Year) + 5*Byte."""
        self.write_short(year)
        self.write_byte(month)
        self.write_byte(day)
        self.write_byte(hour)
        self.write_byte(minute)
        self.write_byte(second)

    def write_date(self, year: int = 2026, month: int = 11, day: int = 3, hour: int = 12, minute: int = 0, second: int = 0):
        """Serializes 7-byte date object format: Short(Year) + 5*Byte."""
        self.write_short(year)
        self.write_byte(month)
        self.write_byte(day)
        self.write_byte(hour)
        self.write_byte(minute)
        self.write_byte(second)

    def write_bytes(self, b: bytes):
        self.buffer.extend(b)

    def get_bytes(self) -> bytes:
        return bytes(self.buffer)


class DDTStreamReader:
    """Helper to deserialize ActionScript 3 ByteArray primitives (Big-Endian)."""
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0

    @property
    def bytes_available(self) -> int:
        return len(self.data) - self.pos

    def read_byte(self) -> int:
        b = self.data[self.pos]
        self.pos += 1
        return struct.unpack('b', bytes([b]))[0]

    def read_ubyte(self) -> int:
        b = self.data[self.pos]
        self.pos += 1
        return b

    def read_boolean(self) -> bool:
        return self.read_ubyte() != 0

    def read_short(self) -> int:
        val = struct.unpack('>h', self.data[self.pos:self.pos+2])[0]
        self.pos += 2
        return val

    def read_ushort(self) -> int:
        val = struct.unpack('>H', self.data[self.pos:self.pos+2])[0]
        self.pos += 2
        return val

    def read_int(self) -> int:
        val = struct.unpack('>i', self.data[self.pos:self.pos+4])[0]
        self.pos += 4
        return val

    def read_uint(self) -> int:
        val = struct.unpack('>I', self.data[self.pos:self.pos+4])[0]
        self.pos += 4
        return val

    def read_long(self) -> int:
        val = struct.unpack('>q', self.data[self.pos:self.pos+8])[0]
        self.pos += 8
        return val

    def read_utf(self) -> str:
        slen = self.read_ushort()
        s = self.data[self.pos:self.pos+slen].decode('utf-8', errors='replace')
        self.pos += slen
        return s

    def read_date_string(self) -> str:
        """Deserializes 7-byte date string: Short(Year) + 5*Byte."""
        year = self.read_short()
        m = self.read_ubyte()
        d = self.read_ubyte()
        h = self.read_ubyte()
        mi = self.read_ubyte()
        s = self.read_ubyte()
        return f"{year}-{m:02d}-{d:02d} {h:02d}:{mi:02d}:{s:02d}"

    def read_date(self) -> Tuple[int, int, int, int, int, int]:
        """Deserializes 7-byte date: Short(Year) + 5*Byte."""
        year = self.read_short()
        m = self.read_ubyte()
        d = self.read_ubyte()
        h = self.read_ubyte()
        mi = self.read_ubyte()
        s = self.read_ubyte()
        return (year, m, d, h, mi, s)

    def read_bytes(self, length: int) -> bytes:
        b = self.data[self.pos:self.pos+length]
        self.pos += length
        return b


class DDTPacket:
    """Represents a discrete DDTank protocol packet."""
    def __init__(self, code: int, client_id: int = 0, extend1: int = 0, extend2: int = 0, payload: bytes = b''):
        self.code = code
        self.client_id = client_id
        self.extend1 = extend1
        self.extend2 = extend2
        self.payload = payload

    def pack(self) -> bytes:
        """
        Serializes packet with 20-byte header, length, and checksum.
        Matches PackageOut::pack.
        """
        total_len = HEADER_SIZE + len(self.payload)
        # Allocate full uncompressed frame
        buf = bytearray(total_len)
        # Bytes 0..1: Magic
        struct.pack_into('>H', buf, 0, HEADER_MAGIC)
        # Bytes 2..3: Total Length
        struct.pack_into('>H', buf, 2, total_len)
        # Bytes 4..5: Checksum (placeholder)
        struct.pack_into('>H', buf, 4, 0)
        # Bytes 6..7: Opcode
        struct.pack_into('>H', buf, 6, self.code)
        # Bytes 8..11: Client ID
        struct.pack_into('>i', buf, 8, self.client_id)
        # Bytes 12..15: Extend1
        struct.pack_into('>i', buf, 12, self.extend1)
        # Bytes 16..19: Extend2
        struct.pack_into('>i', buf, 16, self.extend2)
        # Bytes 20..: Payload
        buf[20:] = self.payload

        # Calculate checksum over bytes [6:]
        chk = calculate_checksum(buf)
        struct.pack_into('>H', buf, 4, chk)

        return bytes(buf)

    @classmethod
    def unpack(cls, data: bytes) -> 'DDTPacket':
        """
        Deserializes a packet from bytes.
        Matches PackageIn::readHeader.
        """
        if len(data) < HEADER_SIZE:
            raise ValueError(f"Packet data too short: {len(data)} < {HEADER_SIZE}")

        magic, total_len, checksum, code, client_id, extend1, extend2 = struct.unpack('>HHHhiii', data[:HEADER_SIZE])
        if magic != HEADER_MAGIC:
            raise ValueError(f"Invalid packet magic 0x{magic:04X} (expected 0x{HEADER_MAGIC:04X})")

        payload = data[HEADER_SIZE:total_len]
        return cls(code=code, client_id=client_id, extend1=extend1, extend2=extend2, payload=payload)

    def __repr__(self):
        return f"<DDTPacket code={self.code} (0x{self.code:04X}) len={len(self.payload)} cid={self.client_id}>"


def serialize_grid_goods(bag_type: int, items: List[Dict[str, Any]], compress: bool = True) -> DDTPacket:
    """
    Serializes ePackageType.GRID_GOODS (Opcode 64 / 0x40).
    Reconstructed from ddt/manager/PlayerManager::__updateInventorySlot.
    Payload is zlib compressed as expected by Flash client pkg.deCompress().
    """
    w = DDTStreamWriter()
    w.write_int(bag_type)
    w.write_int(len(items))

    for it in items:
        place = it.get('place', 0)
        is_exist = bool(it.get('is_exist', 1))

        w.write_int(place)
        w.write_boolean(is_exist)

        if is_exist:
            w.write_int(it.get('user_id', 1))
            w.write_int(it.get('item_id', 1000))
            w.write_int(it.get('count', 1))
            w.write_int(place)
            w.write_int(it.get('template_id', 7014))
            w.write_int(it.get('attack_compose', 0))
            w.write_int(it.get('defend_compose', 0))
            w.write_int(it.get('agility_compose', 0))
            w.write_int(it.get('luck_compose', 0))
            w.write_int(it.get('strengthen_level', 0))
            w.write_int(it.get('strengthen_exp', 0))
            w.write_boolean(bool(it.get('is_bind', 1)))
            w.write_boolean(bool(it.get('is_judge', 1)))
            w.write_date_string(2026, 11, 3, 12, 0, 0)
            w.write_int(it.get('valid_date', 0))
            w.write_utf(it.get('color', ''))
            w.write_utf(it.get('skin', ''))
            w.write_boolean(bool(it.get('is_used', 0)))
            w.write_int(it.get('hole1', -1))
            w.write_int(it.get('hole2', -1))
            w.write_int(it.get('hole3', -1))
            w.write_int(it.get('hole4', -1))
            w.write_int(it.get('hole5', -1))
            w.write_int(it.get('hole6', -1))
            w.write_utf(it.get('pic', ''))
            w.write_int(it.get('refinery_level', 0))
            w.write_date_string(2026, 11, 3, 12, 0, 0)
            w.write_int(it.get('strengthen_times', 0))
            w.write_byte(it.get('hole5_level', 0))
            w.write_int(it.get('hole5_exp', 0))
            w.write_byte(it.get('hole6_level', 0))
            w.write_int(it.get('hole6_exp', 0))
            
            is_gold = bool(it.get('is_gold', 0))
            w.write_boolean(is_gold)
            if is_gold:
                w.write_int(it.get('gold_valid_date', 365))
                w.write_date_string(2026, 11, 3, 12, 0, 0)

            w.write_utf(it.get('latent_energy_cur_str', ''))
            w.write_utf(it.get('latent_energy_new_str', ''))
            w.write_date(2026, 11, 3, 12, 0, 0)

    uncompressed = w.get_bytes()
    payload = zlib.compress(uncompressed) if compress else uncompressed
    return DDTPacket(code=64, payload=payload)


def deserialize_grid_goods(payload: bytes, compressed: bool = True) -> Tuple[int, List[Dict[str, Any]]]:
    """
    Deserializes ePackageType.GRID_GOODS payload into structured item objects.
    Matches Flash client PackageIn::deCompress and __updateInventorySlot loop.
    """
    raw = zlib.decompress(payload) if compressed else payload
    r = DDTStreamReader(raw)
    bag_type = r.read_int()
    item_count = r.read_int()
    items = []

    for _ in range(item_count):
        place = r.read_int()
        is_exist = r.read_boolean()
        if not is_exist:
            items.append({'place': place, 'is_exist': False})
            continue

        item = {
            'place': place,
            'is_exist': True,
            'user_id': r.read_int(),
            'item_id': r.read_int(),
            'count': r.read_int(),
            'place_inner': r.read_int(),
            'template_id': r.read_int(),
            'attack_compose': r.read_int(),
            'defend_compose': r.read_int(),
            'agility_compose': r.read_int(),
            'luck_compose': r.read_int(),
            'strengthen_level': r.read_int(),
            'strengthen_exp': r.read_int(),
            'is_bind': r.read_boolean(),
            'is_judge': r.read_boolean(),
            'begin_date': r.read_date_string(),
            'valid_date': r.read_int(),
            'color': r.read_utf(),
            'skin': r.read_utf(),
            'is_used': r.read_boolean(),
            'hole1': r.read_int(),
            'hole2': r.read_int(),
            'hole3': r.read_int(),
            'hole4': r.read_int(),
            'hole5': r.read_int(),
            'hole6': r.read_int(),
            'pic': r.read_utf(),
            'refinery_level': r.read_int(),
            'discolor_valid_date': r.read_date_string(),
            'strengthen_times': r.read_int(),
            'hole5_level': r.read_byte(),
            'hole5_exp': r.read_int(),
            'hole6_level': r.read_byte(),
            'hole6_exp': r.read_int(),
            'is_gold': r.read_boolean(),
        }

        if item['is_gold']:
            item['gold_valid_date'] = r.read_int()
            item['gold_begin_time'] = r.read_date_string()

        item['latent_energy_cur_str'] = r.read_utf()
        item['latent_energy_new_str'] = r.read_utf()
        item['latent_energy_end_time'] = r.read_date()

        items.append(item)

    return bag_type, items


def serialize_scene_chat(zone_id: int, channel: int, sender: str, msg: str, sender_id: int = 1, is_team: bool = False) -> DDTPacket:
    """
    Serializes ePackageType.SCENE_CHAT (Opcode 19 / 0x13).
    Reconstructed from ddt/manager/ChatManager::__sceneChat.
    """
    w = DDTStreamWriter()
    w.write_int(zone_id)
    w.write_byte(channel)
    w.write_boolean(is_team)
    w.write_utf(sender)
    w.write_utf(msg)
    return DDTPacket(code=19, client_id=sender_id, payload=w.get_bytes())


def deserialize_scene_chat(payload: bytes, client_id: int = 1) -> Dict[str, Any]:
    """Deserializes ePackageType.SCENE_CHAT packet payload."""
    r = DDTStreamReader(payload)
    zone_id = r.read_int()
    channel = r.read_byte()
    is_team = r.read_boolean()
    sender = r.read_utf()
    msg = r.read_utf()
    return {
        'zone_id': zone_id,
        'channel': channel,
        'is_team': is_team,
        'sender': sender,
        'msg': msg,
        'sender_id': client_id
    }


def serialize_room_list(rooms: List[Dict[str, Any]]) -> DDTPacket:
    """
    Serializes GameRoomPackageType.ROOMLIST_UPDATE (Opcode 94, subcode 9).
    Reconstructed from roomList/pvpRoomList/RoomListController::__addRoom.
    """
    w = DDTStreamWriter()
    w.write_byte(9) # subcode = ROOMLIST_UPDATE
    w.write_int(len(rooms)) # roomTotal
    w.write_int(len(rooms)) # count

    for r in rooms:
        w.write_int(r.get('id', 1))
        w.write_byte(r.get('type', 0)) # 0 = MATCH_ROOM, 1 = CHALLENGE_ROOM, 4 = DUNGEON_ROOM
        w.write_byte(r.get('time_type', 1)) # 1 = 5s, 2 = 7s, 3 = 10s
        w.write_byte(r.get('total_player', 2))
        w.write_byte(r.get('viewer_cnt', 0))
        w.write_byte(r.get('max_viewer_cnt', 2))
        w.write_byte(r.get('place_count', 4))
        w.write_boolean(bool(r.get('is_locked', False)))
        w.write_int(r.get('map_id', 1))
        w.write_boolean(bool(r.get('is_playing', False)))
        w.write_utf(r.get('name', 'Sala de Batalha'))
        w.write_byte(r.get('game_mode', 0)) # 0 = Free Mode, 1 = Guild Mode
        w.write_byte(r.get('hard_level', 0))
        w.write_int(r.get('level_limits', 0))

    return DDTPacket(code=94, payload=w.get_bytes())


def serialize_room_create(room: Dict[str, Any]) -> DDTPacket:
    """
    Serializes GameRoomPackageType.GAME_ROOM_CREATE (Opcode 94, subcode 0).
    Reconstructed from room/RoomManager::__createRoom.
    """
    w = DDTStreamWriter()
    w.write_byte(0) # subcode = GAME_ROOM_CREATE
    w.write_int(room.get('id', 1))
    w.write_byte(room.get('type', 0))
    w.write_byte(room.get('hard_level', 0))
    w.write_byte(room.get('time_type', 1))
    w.write_byte(room.get('total_player', 2))
    w.write_byte(room.get('viewer_cnt', 0))
    w.write_byte(room.get('place_count', 4))
    w.write_boolean(bool(room.get('is_locked', False)))
    w.write_int(room.get('map_id', 1))
    w.write_boolean(bool(room.get('started', False)))
    w.write_utf(room.get('name', 'Sala 1'))
    w.write_byte(room.get('game_mode', 0))
    w.write_int(room.get('level_limits', 0))
    w.write_boolean(False) # isCrossZone
    w.write_boolean(False) # isWithinLeageTime
    return DDTPacket(code=94, payload=w.get_bytes())


def serialize_room_add_player(player: Dict[str, Any], is_first_in: bool = True, place: int = 0, team: int = 1, is_host: bool = True) -> DDTPacket:
    """
    Serializes GameRoomPackageType.GAME_ROOM_ADDPLAYER (Opcode 94, subcode 4).
    Reconstructed from room/RoomManager::__addPlayerInRoom.
    """
    w = DDTStreamWriter()
    w.write_byte(4) # subcode = GAME_ROOM_ADDPLAYER
    w.write_boolean(is_first_in)
    w.write_byte(place) # Slot index (0-7)
    w.write_byte(team)  # 1 = Blue Team, 2 = Red Team
    w.write_boolean(is_host)

    # Player Info
    w.write_int(player.get('id', 1))
    w.write_utf(player.get('nickname', 'Player'))
    w.write_byte(1) # typeVIP
    w.write_int(player.get('vip_level', 12))
    w.write_boolean(bool(player.get('sex', 1)))
    w.write_utf(player.get('style', '1142,2101,3105,4101,5101,6101,7014,9002,9002,9022,9022,13101,14001,15001,16001,17002'))
    w.write_utf(player.get('colors', ',,,,,,,,,,,,,,,'))
    w.write_utf(player.get('skin', ''))
    w.write_int(player.get('weapon_id', 7014))
    w.write_int(player.get('deputy_weapon_id', 17002))
    w.write_int(50000) # Repute
    w.write_int(player.get('grade', 65))
    w.write_int(0)     # Offer
    w.write_int(0)     # Hide
    w.write_int(101)   # ConsortiaID
    w.write_utf("DDClássico VIP") # ConsortiaName
    w.write_int(1)     # badgeID
    w.write_int(100)   # WinCount
    w.write_int(110)   # TotalCount
    w.write_int(2)     # EscapeCount
    w.write_long(player.get('fight_power', 450000))
    return DDTPacket(code=94, payload=w.get_bytes())


def serialize_room_player_state(states: List[int]) -> DDTPacket:
    """
    Serializes GameRoomPackageType.GAME_PLAYER_STATE_CHANGE (Opcode 94, subcode 15).
    Reconstructed from room/RoomManager::__playerStateChange.
    states: list of state bytes for each slot (0 = Not Ready, 1 = Ready, 2 = Host).
    """
    w = DDTStreamWriter()
    w.write_byte(15) # subcode = GAME_PLAYER_STATE_CHANGE
    for s in states:
        w.write_byte(s)
    return DDTPacket(code=94, payload=w.get_bytes())


if __name__ == '__main__':
    print("[*] Running DDTank Protocol & Cipher Smoke Tests...")
    
    # Test 1: Checksum verification
    test_buf = bytearray(b'\x71\xab\x00\x18\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04')
    chk = calculate_checksum(test_buf)
    print(f"[*] Checksum test: 0x{chk:04X}")

    # Test 2: Packet pack & unpack round-trip
    writer = DDTStreamWriter()
    writer.write_utf("Antigravity_Test")
    writer.write_int(1337)
    writer.write_boolean(True)
    payload = writer.get_bytes()

    pkg = DDTPacket(code=1, client_id=999, extend1=0, extend2=0, payload=payload)
    packed_raw = pkg.pack()
    print(f"[*] Packed raw size: {len(packed_raw)} bytes (Header: {packed_raw[:20].hex()})")

    unpacked = DDTPacket.unpack(packed_raw)
    assert unpacked.code == 1
    assert unpacked.client_id == 999
    
    reader = DDTStreamReader(unpacked.payload)
    s = reader.read_utf()
    num = reader.read_int()
    b = reader.read_boolean()
    assert s == "Antigravity_Test"
    assert num == 1337
    assert b is True
    print(f"[+] Pack/Unpack Round-Trip: Success! Read string='{s}', int={num}, bool={b}")

    # Test 3: Rolling Byte Cipher Encryption/Decryption Round-Trip
    cipher_enc = DDTStreamCipher()
    cipher_dec = DDTStreamCipher()

    encrypted = cipher_enc.encrypt(packed_raw)
    decrypted = cipher_dec.decrypt(encrypted)

    assert decrypted == packed_raw
    print(f"[+] Stateful Rolling XOR Cipher Round-Trip: Success! ({len(encrypted)} bytes encrypted & decrypted flawlessly)")

    # Test 4: Inventory GRID_GOODS (Opcode 64) Pack & Deserialization
    sample_items = [
        {
            'place': 6, 'is_exist': True, 'user_id': 1, 'item_id': 1007, 'count': 1,
            'template_id': 7014, 'attack_compose': 50, 'defend_compose': 50, 'agility_compose': 50, 'luck_compose': 50,
            'strengthen_level': 12, 'is_bind': True, 'is_judge': True, 'is_gold': True, 'gold_valid_date': 365
        },
        {
            'place': 15, 'is_exist': True, 'user_id': 1, 'item_id': 1016, 'count': 1,
            'template_id': 17002, 'strengthen_level': 12, 'is_bind': True, 'is_judge': True
        }
    ]
    grid_pkt = serialize_grid_goods(bag_type=0, items=sample_items, compress=True)
    assert grid_pkt.code == 64
    packed_grid = grid_pkt.pack()
    
    # Verify unpacking and decompressing
    unpacked_grid = DDTPacket.unpack(packed_grid)
    bag_type_out, items_out = deserialize_grid_goods(unpacked_grid.payload, compressed=True)
    assert bag_type_out == 0
    assert len(items_out) == 2
    assert items_out[0]['template_id'] == 7014
    assert items_out[0]['strengthen_level'] == 12
    assert items_out[0]['is_gold'] is True
    assert items_out[1]['template_id'] == 17002
    print(f"[+] Inventory GRID_GOODS (Opcode 64) Serialization & Decompress: 100% Verified! ({len(packed_grid)} bytes frame)")
