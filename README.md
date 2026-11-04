# DDTank / DDClássico — Reverse Engineering & Authoritative Server Emulator

[![Language](https://img.shields.io/badge/Language-Python%203.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Engine](https://img.shields.io/badge/Engine-7Road%20DDTank%20v2.0.5-orange.svg)]()
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)]()
[![Network](https://img.shields.io/badge/Multiplayer-Tailscale%20VPN-blueviolet.svg)](https://tailscale.com/)

> **A complete reverse engineering and self-contained authoritative server emulator for DDTank (DDClássico v2.0.5 / 7Road ActionScript 3 Engine) written in pure Python.**
> Play locally or online with friends over a zero-config virtual private network (**Tailscale VPN**) without port forwarding.

---

## 📑 Table of Contents
1. [Architecture Overview](#-architecture-overview)
2. [Reverse Engineering Discoveries](#-reverse-engineering-discoveries)
3. [Key Features](#-key-features)
4. [Project Structure](#-project-structure)
5. [Getting Started](#-getting-started)
   - [Prerequisites](#prerequisites)
   - [Hosting a Local Game](#1-hosting-a-local-game-1-click)
   - [Multiplayer with Friends via Tailscale](#2-multiplayer-with-friends-via-tailscale-vpn)
6. [GM Commands](#-gm-commands)
7. [Smoke Testing & Validation](#-smoke-testing--validation)
8. [Documentation & Research](#-documentation--research)
9. [License](#-license)

---

## 🏛️ Architecture Overview

The system emulates the entire 7Road DDTank server stack alongside a decoupled, DRM-free client runtime:

```
                  +----------------------------------------------+
                  |         Decoupled Electron Client            |
                  |  (Chromium 87 + Flash PPAPI 32.0.0.371)      |
                  +-------+-------------------+--------------+---+
                          |                   |              |
                          | TCP :843          | HTTP :8080   | TCP :9200
                          v                   v              v
             +------------+----+     +--------+--------+   +-+---------------+
             | Policy Server   |     | Local CDN Server|   | Game Core Server|
             | (crossdomain.xml|     | (Assets, SWFs,  |   | (Auth, Rooms,   |
             |  Flash Socket)  |     |  XML Templates) |   |  Inventory, GM) |
             +-----------------+     +-----------------+   +--------+--------+
                                                                    |
                                                            +-------v-------+
                                                            | SQLite DB     |
                                                            | (ddtank.db)   |
                                                            +---------------+
```

- **Flash Policy Daemon (`src/ddt_policy_server.py`)**: Listens on `TCP :843` to authorize Adobe Flash Player socket connections.
- **Local Asset CDN (`src/ddt_local_cdn.py`)**: Listens on `HTTP :8080`, hosting static Flash assets (`Loading.swf`, `2.swf`), configuration files, and dynamically responding to missing `.ashx` and `.xml` endpoints. Automatically detects Tailscale IPv4 addresses (`100.x.y.z`).
- **Authoritative Game Core (`src/ddt_server.py`)**: Listens on `TCP :9200`, implementing the stateful rolling XOR stream cipher, session handshakes, SQLite persistence, inventory management, room states, and broadcast chat.
- **CrazyTank Combat Physics Engine (`src/ddt_combat_engine.py`)**: Real-time 2D ballistic calculations, wind drag resistance ($k_w = 0.2$), High Throw ($65^\circ$, $60^\circ$, $20^\circ$) angles, and exponential weapon strengthening formula.
- **Portable Distribution Builder (`src/build_friends_pack.py`)**: Generates a 71 MB standalone ZIP package with zero external dependencies for friends to connect instantly.

---

## 🔬 Reverse Engineering Discoveries

### 1. Themida & Ed25519 Client Decoupling
The official client (`DDClassico.exe`, v2.0.5) utilizes an NSIS wrapper unpacking an Electron runtime protected by **Themida**, **Ed25519 digital signature validation** (`DDREL001` in `release.manifest`), and an AES-256-GCM encrypted package (`DDPACK01` in `launcher.pack`). 

By isolating the Electron 11.5.0 core, Adobe Flash Pepper PPAPI v32.0.0.371 was mounted directly via CLI switches:
```bash
DDClassico.Runtime.exe --ppapi-flash-path="pepflashplayer64.dll" --ppapi-flash-version=32.0.0.371 "http://127.0.0.1:8080/player.html"
```
This bypassed all memory scanning (YARA anti-cheat `ddclassico_scan.dll`) and Themida execution overhead, running the native Flash client at a locked 60 FPS.

### 2. Disguised SWF Core Engine (`2.png` -> `2.swf`)
Static analysis of the CDN traffic showed that client assets ending in `.png` were actually compressed ActionScript 3 SWF containers. Unpacking `2.png` exposed `2.swf` (7.27 MB), containing **2,790 DoABC (AVM2) bytecode blocks**.

### 3. Proprietary 7Road Network Framing & Rolling XOR Cipher
Through automated ABC opcode disassembly of `PackageIn`, `PackageOut`, and `DDTStreamCipher`, the 20-byte framing header and dynamic stream cipher were fully mapped:

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|       Magic (0x71AB)          |         Packet Length         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Checksum             |          Opcode (Code)        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                           Client ID                           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                       Reserved (8 Bytes)                      +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

- **Checksum Formula:**
  $$\text{Checksum} = \left(\sum_{i=0}^{N-1} \text{byte}_i + 119\right) \ \& \ \text{0x7F7F}$$
- **Dynamic Rolling XOR:** Encrypted using an 8-byte stateful key vector:
  $$\text{Key}_0 = [\text{0xAE}, \text{0xBF}, \text{0x56}, \text{0x78}, \text{0xAB}, \text{0xCD}, \text{0xEF}, \text{0xF1}]$$
  Each encrypted byte updates the state key using rolling addition and bitwise shifts.

### 4. Mandatory ZLIB Compression for `GRID_GOODS`
Disassembly of `PlayerManager::__updateInventorySlot` (Method ID 8) revealed an unconditional call to `pkg.deCompress()` before parsing slot counts. All inventory payloads **must be compressed with ZLIB** prior to packet framing; otherwise, the client aborts with ActionScript `Error #2058`.

### 5. Weapon Strengthening Scaling (`StaticFormula`)
Decompiled formulas from `ddt.utils.StaticFormula` prove that attributes scale exponentially:
$$\text{Attribute}_{\text{level}} = \text{Base} \times (1.1)^{\text{level}}$$
A +12 weapon multiplies base damage and attributes by $3.1384\times$ ($+213.8\%$).

---

## ✨ Key Features

- **Authoritative Local Hosting:** Complete server stack in pure Python 3 without requiring external databases or third-party engines.
- **Tailscale VPN Multiplayer:** Seamlessly invite friends over a secure virtual mesh network (`100.x.y.z`) without opening ports on your home router.
- **VIP Arsenal Preloaded:** Accounts are initialized at **Level 65, VIP 12, 9,999,999 Gold/Cash/EXP**, and 27 legendary +12 weapons/accessories:
  - Super Bumerangue +12 (7014) & Super Quebra-Tijolos +12 (7004)
  - Verdadeiro Dom de Anjo +12 (17002)
  - Coroa Real (1142) & Armadura de Ouro (5101) & Asas Fênix (15001)
  - Anéis da Felicidade +5 & Braceletes de Vênus +5 & 999x Pedras Fortalecimento Nv. 5
- **Multi-Client Lobby & Rooms:** Real-time room creation, joining, player state synchronization (Ready/Not Ready), and map selection.
- **In-Game GM Console:** Full admin controls directly through the in-game scene chat (`/item`, `/gold`, `/money`, `/level`).

---

## 📂 Project Structure

```
projects/ddtank-server/
├── README.md                          # Project documentation
├── LICENSE                            # MIT License
├── DDTank_Launcher.bat                # 1-Click launcher (Servers + Client)
├── launch_server.bat                  # Dedicated server launcher
├── launch_client.bat                  # Client launcher
├── data/
│   ├── ddtank.db                      # SQLite persistence (users, items)
│   └── ddt_protocol_schema.json       # 1,259 opcodes/constants
├── src/
│   ├── ddt_protocol.py                # 7Road packet framing, checksum & cipher
│   ├── ddt_server.py                  # Core authoritative game server (TCP 9200)
│   ├── ddt_policy_server.py           # Flash socket policy server (TCP 843)
│   ├── ddt_local_cdn.py               # Local asset CDN & fallback (HTTP 8080)
│   ├── ddt_combat_engine.py           # 2D ballistics & damage physics engine
│   ├── ddt_cluster_manager.py         # Multi-process orchestrator
│   └── build_friends_pack.py          # Portable friends distribution builder
├── tests/
│   ├── test_server_smoke.py           # Handshake and login smoke test
│   ├── test_inventory_smoke.py        # ZLIB inventory smoke test
│   └── test_lobby_smoke.py            # Multi-client lobby and chat smoke test
├── tools/
│   ├── setup_inventory_db.py          # VIP arsenal database seeder
│   ├── generate_xml_templates.py      # Authoritative XML templates builder
│   ├── extract_protocol_schema.py     # SWF DoABC opcode extractor
│   └── unpack_asar.py                 # Pure Python Electron ASAR unpacker
├── research/
│   └── probes/                        # 30+ disassembler and memory probes
├── docs/
│   ├── REVERSE_ENGINEERING_ARCHITECTURE.md
│   └── PROTOCOL_SPECIFICATION.md
└── www/                               # Web and Flash assets
    ├── player.html                    # Web player entrypoint
    ├── flash/                         # SWF modules (Loading.swf, 2.swf)
    └── request/                       # XML templates (TemplateAllList.xml, etc.)
```

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+** installed on the host machine.
- Windows 10/11 (64-bit).
- [Tailscale](https://tailscale.com/) installed (for playing online with friends).

### 1. Hosting a Local Game (1-Click)
Simply run:
```bash
DDTank_Launcher.bat
```
This automatically starts the Policy Server, Asset CDN, and Game Server, and launches the desktop Flash client.

The local player starts with `www/flash/DDT_Loading.swf`, the normal login loader.
Keep this file with the other Flash assets: the older `Loading.swf` can send the
client into the first-login trainer, whose download ends at 70% before the game
core is requested. The preconfigured Admin profile must retain `IsFirst="2"`
in `www/request/LoginSelectList.ashx` to use normal login.
The CDN encodes tables for this loader with zlib and XOR over the first 1024
bytes. Localized requests such as `/request/portugal/TemplateAllList.xml` use
the exported tables in `www/request/`. `MapServerList.xml` is a compressed map
table with `ServerID` and `OpenMap` attributes; the channel list and the pet/totem
tables consumed by `TextLoader` stay plain XML.
Login dates must use `YYYY-MM-DDTHH:MM:SS`, as required by the Flash date parser.

### 2. Multiplayer with Friends (via Tailscale VPN)

1. **Host Setup:**
   - Install and log in to [Tailscale](https://tailscale.com/). Note your Tailscale IPv4 address (e.g. `100.115.82.41`).
   - Run `DDTank_Launcher.bat` on your PC.

2. **Generate Friends Distribution Pack:**
   Run the distribution builder:
   ```bash
   python src/build_friends_pack.py
   ```
   This generates `dist/DDTank_Multiplayer_Amigos.zip` (71 MB), fully portable and decoupled from Themida.

3. **Friends Setup:**
   - Your friends join your Tailscale tailnet.
   - Send them `DDTank_Multiplayer_Amigos.zip`.
   - They extract the ZIP and double-click **`Jogar_Online.bat`**.
   - When prompted, they enter your Tailscale IP (`100.115.82.41`). The game connects instantly!

---

## 💬 GM Commands

Type these commands directly into the in-game scene chat:

| Command | Syntax | Description |
| :--- | :--- | :--- |
| `/help` | `/help` | Displays available GM commands |
| `/gold` | `/gold <amount>` | Adds Gold to your character |
| `/money` | `/money <amount>` | Adds Cash/Money to your character |
| `/level` | `/level <level>` | Sets character level (1 to 65) |
| `/item` | `/item <template_id> [qty]` | Instantly grants any item (e.g. `/item 7004 1` for Super Quebra-Tijolos) |

---

## 🧪 Smoke Testing & Validation

The test suite validates protocol compliance and multi-client synchronization:

```bash
# 1. Run unit tests for protocol framing, cipher & ZLIB compression:
python src/ddt_protocol.py

# 2. Run combat physics & ballistics engine simulation:
python src/ddt_combat_engine.py

# 3. Multi-client lobby & GM command integration test:
python tests/test_lobby_smoke.py

# 4. Local startup assets, HTTP responses, and Flash table decoding:
python -m unittest discover -s tests -p "test_cdn_loading.py" -v
```

---

## 📖 Documentation & Research

- **[Reverse Engineering Architecture](docs/REVERSE_ENGINEERING_ARCHITECTURE.md)**: Comprehensive deep-dive covering memory probing, Themida bypass, ActionScript 3 disassembling, and network state machines.
- **[Protocol Specification](docs/PROTOCOL_SPECIFICATION.md)**: Complete catalog of packet framing, opcodes, and data type encodings.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE). Built for educational, preservation, and research purposes.
