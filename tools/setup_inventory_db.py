"""
Setup DDTank Inventory & VIP Arsenal Database
Target: DDClássico (ddclassico.com) v2.0.5 / 7Road DDTank Engine
Creates 'items' table in targets/dd-classico/data/ddtank.db and seeds authoritative VIP Arsenal.
"""

import os
import sqlite3

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH = os.path.join(BASE_DIR, 'data', 'ddtank.db')

def init_items_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        template_id INTEGER NOT NULL,
        bag_type INTEGER NOT NULL,
        place INTEGER NOT NULL,
        count INTEGER DEFAULT 1,
        is_exist INTEGER DEFAULT 1,
        strengthen_level INTEGER DEFAULT 0,
        strengthen_exp INTEGER DEFAULT 0,
        attack_compose INTEGER DEFAULT 0,
        defend_compose INTEGER DEFAULT 0,
        agility_compose INTEGER DEFAULT 0,
        luck_compose INTEGER DEFAULT 0,
        is_bind INTEGER DEFAULT 1,
        is_judge INTEGER DEFAULT 1,
        valid_date INTEGER DEFAULT 0,
        color TEXT DEFAULT '',
        skin TEXT DEFAULT '',
        is_used INTEGER DEFAULT 0,
        hole1 INTEGER DEFAULT -1,
        hole2 INTEGER DEFAULT -1,
        hole3 INTEGER DEFAULT -1,
        hole4 INTEGER DEFAULT -1,
        hole5 INTEGER DEFAULT -1,
        hole6 INTEGER DEFAULT -1,
        hole5_level INTEGER DEFAULT 0,
        hole5_exp INTEGER DEFAULT 0,
        hole6_level INTEGER DEFAULT 0,
        hole6_exp INTEGER DEFAULT 0,
        is_gold INTEGER DEFAULT 0,
        gold_valid_date INTEGER DEFAULT 0,
        refinery_level INTEGER DEFAULT 0,
        strengthen_times INTEGER DEFAULT 0,
        latent_energy_cur_str TEXT DEFAULT '',
        latent_energy_new_str TEXT DEFAULT '',
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    conn.commit()
    conn.close()
    print("[+] Table 'items' verified/created.")

def seed_vip_arsenal(user_id=1):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM items WHERE user_id = ?", (user_id,))

    items = [
        # Equipados (Bag 0: EQUIPBAG, Places 0-15)
        {"item_id": 1001, "template_id": 1142, "bag_type": 0, "place": 0, "strengthen_level": 12, "attack_compose": 50, "defend_compose": 50, "agility_compose": 50, "luck_compose": 50},  # Chapéu
        {"item_id": 1002, "template_id": 2101, "bag_type": 0, "place": 1, "strengthen_level": 0},   # Óculos
        {"item_id": 1003, "template_id": 3105, "bag_type": 0, "place": 2, "strengthen_level": 0},   # Cabelo
        {"item_id": 1004, "template_id": 4101, "bag_type": 0, "place": 3, "strengthen_level": 0},   # Olhos
        {"item_id": 1005, "template_id": 5101, "bag_type": 0, "place": 4, "strengthen_level": 12, "attack_compose": 50, "defend_compose": 50, "agility_compose": 50, "luck_compose": 50},  # Roupa
        {"item_id": 1006, "template_id": 6101, "bag_type": 0, "place": 5, "strengthen_level": 0},   # Rosto
        {"item_id": 1007, "template_id": 7014, "bag_type": 0, "place": 6, "strengthen_level": 12, "is_gold": 1, "gold_valid_date": 365, "attack_compose": 50, "defend_compose": 50, "agility_compose": 50, "luck_compose": 50}, # Arma: Super Bumerangue Dourado +12
        {"item_id": 1008, "template_id": 9002, "bag_type": 0, "place": 7, "strengthen_level": 5},   # Bracelete 1 (+5)
        {"item_id": 1009, "template_id": 9002, "bag_type": 0, "place": 8, "strengthen_level": 5},   # Bracelete 2 (+5)
        {"item_id": 1010, "template_id": 9022, "bag_type": 0, "place": 9, "strengthen_level": 5},   # Anel 1 (+5)
        {"item_id": 1011, "template_id": 9022, "bag_type": 0, "place": 10, "strengthen_level": 5},  # Anel 2 (+5)
        {"item_id": 1012, "template_id": 13101, "bag_type": 0, "place": 11, "strengthen_level": 0}, # Traje Campeão
        {"item_id": 1013, "template_id": 14001, "bag_type": 0, "place": 12, "strengthen_level": 0}, # Colar Cristal
        {"item_id": 1014, "template_id": 15001, "bag_type": 0, "place": 13, "strengthen_level": 0}, # Asas Fênix
        {"item_id": 1015, "template_id": 16001, "bag_type": 0, "place": 14, "strengthen_level": 0}, # Bolha Chat VIP
        {"item_id": 1016, "template_id": 17002, "bag_type": 0, "place": 15, "strengthen_level": 12}, # Offhand: Verdadeiro Dom de Anjo +12

        # Mochila de Equipamentos Reserva (Bag 0: EQUIPBAG, Places 31-36)
        {"item_id": 1017, "template_id": 7015, "bag_type": 0, "place": 31, "strengthen_level": 12, "is_gold": 1, "gold_valid_date": 365, "attack_compose": 50, "defend_compose": 50, "agility_compose": 50, "luck_compose": 50}, # Super Dom de Amor
        {"item_id": 1018, "template_id": 7004, "bag_type": 0, "place": 32, "strengthen_level": 12, "attack_compose": 50, "defend_compose": 50, "agility_compose": 50, "luck_compose": 50}, # Super Quebra-Tijolos
        {"item_id": 1019, "template_id": 7008, "bag_type": 0, "place": 33, "strengthen_level": 12, "attack_compose": 50, "defend_compose": 50, "agility_compose": 50, "luck_compose": 50}, # Super Lança do Trovão
        {"item_id": 1020, "template_id": 7001, "bag_type": 0, "place": 34, "strengthen_level": 12, "attack_compose": 50, "defend_compose": 50, "agility_compose": 50, "luck_compose": 50}, # Super Canhão de Mão
        {"item_id": 1021, "template_id": 7010, "bag_type": 0, "place": 35, "strengthen_level": 12, "attack_compose": 50, "defend_compose": 50, "agility_compose": 50, "luck_compose": 50}, # Super Fogos de Artifício
        {"item_id": 1022, "template_id": 17003, "bag_type": 0, "place": 36, "strengthen_level": 12}, # Verdadeiro Escudo de Barok +12

        # Mochila de Consumíveis e Pedras (Bag 1: PROPBAG, Places 0-4)
        {"item_id": 2001, "template_id": 11023, "bag_type": 1, "place": 0, "count": 999}, # Pedra Fortalecimento Nv. 5
        {"item_id": 2002, "template_id": 11018, "bag_type": 1, "place": 1, "count": 999}, # Amuleto da Sorte 25%
        {"item_id": 2003, "template_id": 11020, "bag_type": 1, "place": 2, "count": 999}, # Símbolo dos Deuses
        {"item_id": 2004, "template_id": 11101, "bag_type": 1, "place": 3, "count": 999}, # Megafone Pequeno
        {"item_id": 2005, "template_id": 11102, "bag_type": 1, "place": 4, "count": 999}, # Megafone Grande
    ]

    for it in items:
        c.execute("""
        INSERT INTO items (
            user_id, item_id, template_id, bag_type, place, count, is_exist,
            strengthen_level, strengthen_exp, attack_compose, defend_compose, agility_compose, luck_compose,
            is_bind, is_judge, valid_date, color, skin, is_used,
            hole1, hole2, hole3, hole4, hole5, hole6, hole5_level, hole5_exp, hole6_level, hole6_exp,
            is_gold, gold_valid_date, refinery_level, strengthen_times,
            latent_energy_cur_str, latent_energy_new_str
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?
        )
        """, (
            user_id, it["item_id"], it["template_id"], it["bag_type"], it["place"], it.get("count", 1), 1,
            it.get("strengthen_level", 0), 0, it.get("attack_compose", 0), it.get("defend_compose", 0), it.get("agility_compose", 0), it.get("luck_compose", 0),
            1, 1, 0, "", "", 1 if it["bag_type"] == 0 and it["place"] < 16 else 0,
            -1, -1, -1, -1, -1, -1, 0, 0, 0, 0,
            it.get("is_gold", 0), it.get("gold_valid_date", 0), 0, 0,
            "", ""
        ))

    conn.commit()
    conn.close()
    print(f"[+] Seeded {len(items)} VIP Arsenal items for user {user_id}.")

if __name__ == '__main__':
    print("[*] Initializing DDTank Inventory Database...")
    init_items_table()
    seed_vip_arsenal(1)
    print("[+] DDTank Inventory DB setup completed successfully!")
