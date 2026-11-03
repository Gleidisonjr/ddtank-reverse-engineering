"""
Generate DDTank XML Configuration & Template Files
Target: DDClássico (ddclassico.com) v2.0.5 / 7Road DDTank Engine
Generates complete authoritative XML files in targets/dd-classico/www/request/
"""

import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
REQUEST_DIR = os.path.join(BASE_DIR, 'targets', 'dd-classico', 'www', 'request')
os.makedirs(REQUEST_DIR, exist_ok=True)

def write_xml(filename, content):
    path = os.path.join(REQUEST_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')
    print(f"[+] Generated {path} ({len(content)} bytes)")

def generate_categories():
    categories = [
        (1, "Chapéu", 0, "Head"),
        (2, "Óculos", 1, "Glass"),
        (3, "Cabelo", 2, "Hair"),
        (4, "Olhos", 3, "Eff"),
        (5, "Roupa", 4, "Cloth"),
        (6, "Rosto", 5, "Face"),
        (7, "Arma", 6, "Arm"),
        (8, "Bracelete", 7, "Armlet"),
        (9, "Anel", 9, "Ring"),
        (11, "Item de Uso", 0, "Prop"),
        (12, "Missão", 0, "Task"),
        (13, "Terno", 11, "Suits"),
        (14, "Colar", 12, "Necklace"),
        (15, "Asas", 13, "Wing"),
        (16, "Bolha", 14, "ChatBall"),
        (17, "Arma Secundária", 15, "Offhand"),
        (18, "Cartas", 0, "Cards"),
        (19, "Pedra de Cura", 0, "HealStone"),
        (20, "Prática", 0, "Texp"),
        (31, "Especial", 0, "Special"),
        (34, "Comida de Pet", 0, "PetFood"),
        (35, "Ovo de Pet", 0, "PetEgg"),
        (50, "Arma Pet", 0, "PetArm"),
        (51, "Chapéu Pet", 0, "PetHead"),
        (52, "Roupa Pet", 0, "PetCloth"),
    ]
    lines = ['<?xml version="1.0" encoding="utf-8" ?>', '<Result value="true" message="Success">']
    for cid, name, place, remark in categories:
        lines.append(f'    <Item ID="{cid}" Name="{name}" Place="{place}" Remark="{remark}" />')
    lines.append('</Result>')
    write_xml("LoadItemsCategory.xml", "\n".join(lines))

def generate_templates():
    items = [
        # Armas Principais (CategoryID = 7)
        {"TemplateID": 7014, "Name": "Super Bumerangue do Amor", "CategoryID": 7, "Attack": 250, "Defence": 200, "Agility": 250, "Luck": 200, "NeedSex": 0, "Quality": 5, "Pic": "arm/boomerang", "Description": "Arma Lendária de longo alcance com retorno garantido e alto poder de destruição."},
        {"TemplateID": 7015, "Name": "Super Dom de Amor", "CategoryID": 7, "Attack": 240, "Defence": 240, "Agility": 240, "Luck": 240, "NeedSex": 0, "Quality": 5, "Pic": "arm/giftbox", "Description": "Espalha amor e explosões massivas por todo o campo de batalha."},
        {"TemplateID": 7004, "Name": "Super Quebra-Tijolos", "CategoryID": 7, "Attack": 280, "Defence": 260, "Agility": 160, "Luck": 180, "NeedSex": 0, "Quality": 4, "Pic": "arm/brick", "Description": "Pesado, destrutivo e implacável para cavar crateras gigantes."},
        {"TemplateID": 7008, "Name": "Super Lança do Trovão", "CategoryID": 7, "Attack": 270, "Defence": 190, "Agility": 260, "Luck": 220, "NeedSex": 0, "Quality": 4, "Pic": "arm/spear", "Description": "Ataques rápidos como o relâmpago, com alta taxa de acerto crítico."},
        {"TemplateID": 7001, "Name": "Super Canhão de Mão", "CategoryID": 7, "Attack": 290, "Defence": 210, "Agility": 180, "Luck": 200, "NeedSex": 0, "Quality": 4, "Pic": "arm/cannon", "Description": "Canhão clássico de cerco com disparos de alto calibre."},
        {"TemplateID": 7010, "Name": "Super Fogos de Artifício", "CategoryID": 7, "Attack": 230, "Defence": 210, "Agility": 270, "Luck": 250, "NeedSex": 0, "Quality": 4, "Pic": "arm/firework", "Description": "Espetáculo de cores com altíssima agilidade e sorte."},

        # Armas Secundárias (CategoryID = 17)
        {"TemplateID": 17002, "Name": "Verdadeiro Dom de Anjo", "CategoryID": 17, "Attack": 0, "Defence": 100, "Agility": 50, "Luck": 100, "NeedSex": 0, "Quality": 5, "Pic": "arm/angel", "Property2": 1500, "Description": "Recupera 1500 de vida por turno de uso."},
        {"TemplateID": 17003, "Name": "Verdadeiro Escudo de Barok", "CategoryID": 17, "Attack": 0, "Defence": 250, "Agility": 0, "Luck": 50, "NeedSex": 0, "Quality": 5, "Pic": "arm/shield", "Property2": 500, "Description": "Reduz o dano recebido em até 500 pontos."},

        # Chapéus (CategoryID = 1)
        {"TemplateID": 1142, "Name": "Coroa Real Imperial", "CategoryID": 1, "Attack": 50, "Defence": 80, "Agility": 50, "Luck": 60, "NeedSex": 0, "Quality": 5, "Pic": "head/crown", "Description": "Coroa reluzente símbolo de poder máximo."},

        # Roupas (CategoryID = 5)
        {"TemplateID": 5101, "Name": "Armadura de Ouro Solar", "CategoryID": 5, "Attack": 60, "Defence": 100, "Agility": 60, "Luck": 60, "NeedSex": 0, "Quality": 5, "Pic": "cloth/golden_armor", "Description": "Armadura forjada no fogo sagrado com defesa impenetrável."},

        # Cabelos (CategoryID = 3)
        {"TemplateID": 3105, "Name": "Cabelo Espetado Estiloso", "CategoryID": 3, "Attack": 20, "Defence": 20, "Agility": 30, "Luck": 30, "NeedSex": 1, "Quality": 3, "Pic": "hair/spiky", "Description": "Visual moderno e arrojado."},

        # Óculos (CategoryID = 2)
        {"TemplateID": 2101, "Name": "Óculos Escuros VIP", "CategoryID": 2, "Attack": 25, "Defence": 25, "Agility": 40, "Luck": 40, "NeedSex": 0, "Quality": 4, "Pic": "glass/shades", "Description": "Elegância pura na linha de tiro."},

        # Olhos / Expressões (CategoryID = 4)
        {"TemplateID": 4101, "Name": "Olhar Penetrante de Batalha", "CategoryID": 4, "Attack": 15, "Defence": 15, "Agility": 25, "Luck": 25, "NeedSex": 0, "Quality": 3, "Pic": "eff/fierce_eyes", "Description": "Foco inabalável no alvo."},

        # Pintura Facial (CategoryID = 6)
        {"TemplateID": 6101, "Name": "Pintura de Guerra Feroz", "CategoryID": 6, "Attack": 30, "Defence": 20, "Agility": 30, "Luck": 30, "NeedSex": 0, "Quality": 4, "Pic": "face/warpaint", "Description": "Intimida adversários à primeira vista."},

        # Ternos / Sets (CategoryID = 13)
        {"TemplateID": 13101, "Name": "Traje Lendário do Campeão", "CategoryID": 13, "Attack": 80, "Defence": 80, "Agility": 80, "Luck": 80, "NeedSex": 0, "Quality": 5, "Pic": "suits/champion", "Description": "A vestimenta dos verdadeiros mestres do DDTank."},

        # Asas (CategoryID = 15)
        {"TemplateID": 15001, "Name": "Asas Flamejantes do Fênix", "CategoryID": 15, "Attack": 60, "Defence": 60, "Agility": 100, "Luck": 80, "NeedSex": 0, "Quality": 5, "Pic": "wing/phoenix", "Description": "Proporcionam agilidade sublime e elegância nos ares."},

        # Colares (CategoryID = 14)
        {"TemplateID": 14001, "Name": "Colar de Cristal de Sangue", "CategoryID": 14, "Attack": 0, "Defence": 0, "Agility": 0, "Luck": 0, "NeedSex": 0, "Quality": 5, "Pic": "necklace/blood_crystal", "Property1": 50, "Description": "Aumenta o HP máximo do portador em 50%."},

        # Braceletes (CategoryID = 8)
        {"TemplateID": 9002, "Name": "Bracelete de Vênus +5", "CategoryID": 8, "Attack": 55, "Defence": 55, "Agility": 55, "Luck": 55, "NeedSex": 0, "Quality": 5, "Pic": "armlet/venus", "Description": "Aumenta todos os quatro atributos básicos simultaneamente."},

        # Anéis (CategoryID = 9)
        {"TemplateID": 9022, "Name": "Anel da Felicidade +5", "CategoryID": 9, "Attack": 60, "Defence": 60, "Agility": 60, "Luck": 60, "NeedSex": 0, "Quality": 5, "Pic": "ring/happiness", "Description": "Anel lendário repleto de boas energias e poder devastador."},

        # Bolhas de Chat (CategoryID = 16)
        {"TemplateID": 16001, "Name": "Bolha de Chat Dourada VIP", "CategoryID": 16, "Attack": 10, "Defence": 10, "Agility": 10, "Luck": 10, "NeedSex": 0, "Quality": 4, "Pic": "chatball/gold", "Description": "Destaque suas mensagens no chat com bordas douradas reluzentes."},

        # Consumíveis & Pedras (CategoryID = 11)
        {"TemplateID": 11023, "Name": "Pedra de Fortalecimento Nv. 5", "CategoryID": 11, "NeedSex": 0, "Quality": 5, "MaxCount": 999, "Pic": "prop/stone5", "Description": "Pedra mágica de alta pureza utilizada para aprimorar armas até +12."},
        {"TemplateID": 11018, "Name": "Amuleto da Sorte 25%", "CategoryID": 11, "NeedSex": 0, "Quality": 4, "MaxCount": 999, "Pic": "prop/charm25", "Description": "Aumenta em 25% a taxa de sucesso no fortalecimento."},
        {"TemplateID": 11020, "Name": "Símbolo dos Deuses", "CategoryID": 11, "NeedSex": 0, "Quality": 4, "MaxCount": 999, "Pic": "prop/symbol", "Description": "Protege seu equipamento contra perda de nível em caso de falha."},
        {"TemplateID": 11101, "Name": "Megafone Pequeno", "CategoryID": 11, "NeedSex": 0, "Quality": 2, "MaxCount": 999, "Pic": "prop/sbugle", "Description": "Transmite mensagem para todo o canal atual."},
        {"TemplateID": 11102, "Name": "Megafone Grande", "CategoryID": 11, "NeedSex": 0, "Quality": 3, "MaxCount": 999, "Pic": "prop/bbugle", "Description": "Transmite mensagem destacada para todos os canais e servidores."},
    ]

    lines = ['<?xml version="1.0" encoding="utf-8" ?>', '<Result value="true" message="Success">']
    for it in items:
        attrs = [
            f'TemplateID="{it["TemplateID"]}"',
            f'Name="{it["Name"]}"',
            f'CategoryID="{it["CategoryID"]}"',
            f'Attack="{it.get("Attack", 0)}"',
            f'Defence="{it.get("Defence", 0)}"',
            f'Agility="{it.get("Agility", 0)}"',
            f'Luck="{it.get("Luck", 0)}"',
            f'NeedLevel="1"',
            f'NeedSex="{it.get("NeedSex", 0)}"',
            f'Quality="{it.get("Quality", 4)}"',
            f'Pic="{it.get("Pic", "")}"',
            f'MaxCount="{it.get("MaxCount", 1)}"',
            f'Description="{it.get("Description", "")}"',
            f'CanDrop="false"',
            f'CanDelete="false"',
            f'CanEquip="true"',
            f'CanUse="true"',
            f'CanStrengthen="true"',
            f'CanCompose="true"',
            f'Hole="1,1,1,1,1,1"',
            f'RefineryLevel="0"',
            f'BindType="1"',
            f'Property1="{it.get("Property1", 0)}"',
            f'Property2="{it.get("Property2", 0)}"',
            f'Property3="0"',
            f'Property4="0"',
            f'Property5="0"',
            f'Property6="0"',
            f'Property7="0"',
            f'Property8="0"'
        ]
        lines.append(f'    <ItemTemplate {" ".join(attrs)} />')
    lines.append('</Result>')
    write_xml("TemplateAllList.xml", "\n".join(lines))

def generate_balls():
    balls = [
        {"ID": 1, "Name": "Canhão Padrão", "Crater": "1", "BombPartical": "1", "FlyingPartical": "1", "blastOutID": 1, "craterID": 1},
        {"ID": 2, "Name": "Bumerangue", "Crater": "2", "BombPartical": "2", "FlyingPartical": "2", "blastOutID": 2, "craterID": 2},
        {"ID": 3, "Name": "Quebra-Tijolos", "Crater": "3", "BombPartical": "3", "FlyingPartical": "3", "blastOutID": 3, "craterID": 3},
        {"ID": 4, "Name": "Lança Trovão", "Crater": "4", "BombPartical": "4", "FlyingPartical": "4", "blastOutID": 4, "craterID": 4},
        {"ID": 5, "Name": "Dom de Amor", "Crater": "5", "BombPartical": "5", "FlyingPartical": "5", "blastOutID": 5, "craterID": 5},
        {"ID": 64, "Name": "Tiro Triplo (+2)", "Crater": "1", "BombPartical": "1", "FlyingPartical": "1", "blastOutID": 1, "craterID": 1},
        {"ID": 87, "Name": "Laser / Especial", "Crater": "87", "BombPartical": "87", "FlyingPartical": "87", "blastOutID": 87, "craterID": 87},
    ]
    lines = ['<?xml version="1.0" encoding="utf-8" ?>', '<Result value="true" message="Success">']
    for b in balls:
        attrs = [f'{k}="{v}"' for k, v in b.items()]
        lines.append(f'    <Item {" ".join(attrs)} />')
    lines.append('</Result>')
    write_xml("BallList.xml", "\n".join(lines))

def generate_server_config():
    xml = """<?xml version="1.0" encoding="utf-8" ?>
<Result value="true" message="Success">
    <Item Name="VIPLevelExp" Value="0,100,500,1500,3500,7000,12000,18000,25000,35000,50000,80000" />
    <Item Name="MaxLevel" Value="65" />
    <Item Name="FightPowerRate" Value="1.0" />
    <Item Name="CanBuyProp" Value="true" />
    <Item Name="AutoOpenHole" Value="true" />
</Result>
"""
    write_xml("ServerConfig.xml", xml)

def generate_maps():
    maps = [
        {"ID": 1, "Name": "Vila das Fadas", "Type": 1, "Description": "Mapa clássico verdejante", "Pic": "map/1"},
        {"ID": 2, "Name": "Castelo Antigo", "Type": 1, "Description": "Ruínas medievais", "Pic": "map/2"},
        {"ID": 3, "Name": "Laboratório Secreto", "Type": 1, "Description": "Complexo subterrâneo de alta tecnologia", "Pic": "map/3"},
        {"ID": 4, "Name": "Deserto dos Ventos", "Type": 1, "Description": "Dunas escaldantes sob fortes correntes de ar", "Pic": "map/4"},
    ]
    lines = ['<?xml version="1.0" encoding="utf-8" ?>', '<Result value="true" message="Success">']
    for m in maps:
        attrs = [f'{k}="{v}"' for k, v in m.items()]
        lines.append(f'    <Item {" ".join(attrs)} />')
    lines.append('</Result>')
    write_xml("MapServerList.xml", "\n".join(lines))

def generate_levels():
    lines = ['<?xml version="1.0" encoding="utf-8" ?>', '<Result value="true" message="Success">']
    exp = 0
    for lvl in range(1, 66):
        exp += lvl * 1000
        lines.append(f'    <Item Grade="{lvl}" GP="{exp}" Blood="1000" />')
    lines.append('</Result>')
    write_xml("LevelList.xml", "\n".join(lines))

def generate_generic_stubs():
    stubs = [
        "BombConfig.xml",
        "QuestList.xml",
        "ShopItemList.xml",
        "ShopGoodsShowList.xml",
        "CardInfoList.xml",
        "VipSettingList.xml",
        "DailyAwardList.xml",
        "PetTemplateInfo.xml",
        "SuitTemplateInfoList.xml",
        "SuitEquipList.xml",
        "ItemStrengthenGoodsInfo.xml",
        "LoadMapsItems.xml",
        "LoadPVEItems.xml",
        "LoadBoxTemp.xml",
    ]
    xml = """<?xml version="1.0" encoding="utf-8" ?>
<Result value="true" message="Success">
</Result>
"""
    for s in stubs:
        write_xml(s, xml)

if __name__ == '__main__':
    print("[*] Generating DDTank Authoritative XML Templates...")
    generate_categories()
    generate_templates()
    generate_balls()
    generate_server_config()
    generate_maps()
    generate_levels()
    generate_generic_stubs()
    print("[+] All XML configuration templates successfully generated!")
