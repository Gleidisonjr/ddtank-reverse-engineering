# DDTank ActionScript 3 Core Engine & Protocol Reverse Engineering
**Alvo:** DDClássico (`ddclassico.com` v2.0.5) / 7Road DDTank Flash Engine  
**Data:** 2026-11-03  
**Status:** Concluído com Sucesso  
**Ativos Analisados:** `targets/dd-classico/extracted/dumped/flash_assets/2.swf` (7,27 MB descompactado de `2.png`), `Loading.swf`, `DDT_Loading.swf`

---

## 1. Visão Geral da Arquitetura ActionScript 3 (AVM2)

O cliente DDClássico emprega o runtime Adobe Flash Player Pepper (PPAPI v32.0.0.371) embutido no Electron via flag `--ppapi-flash-path`. Todos os módulos centrais de física, balística, rede, interface e telemetria foram empacotados em um único arquivo binário disguised (`2.png`), que ao ser descompactado revelou `2.swf` (7.273.204 bytes / 7,27 MB).

### Estrutura de Tags SWF do `2.swf`:
- **Tags Totais:** 2.798 tags SWF.
- **Blocos DoABC (Tag 82 / 0x52):** **2.790 tags DoABC independentes**, onde cada classe ou módulo compilado do ActionScript 3 (AVM2) possui seu próprio bytecode, tabela de constantes, métodos e traits.
- **Formatos Auxiliares:** Tags de metadados (`<rdf:RDF>`), `FileAttributes` (Tag 69) e `SymbolClass` (Tag 76).

---

## 2. Protocolo de Rede Mestre (7Road ByteSocket & Framing)

A comunicação de jogo do DDTank é baseada em sockets TCP binários persistentes operados pelas classes `road7th.comm.ByteSocket`, `road7th.comm.PackageIn` e `road7th.comm.PackageOut`.

### 2.1. Estrutura do Cabeçalho de Pacote (20 Bytes Big-Endian)

Todo pacote de rede do DDTank inicia com um cabeçalho fixo de 20 bytes:

| Offset | Tipo | Campo | Descrição |
|---|---|---|---|
| `0..1` | `uint16` | `HEADER_MAGIC` | Número mágico fixo: **`0x71AB`** (decimal: `29099`). |
| `2..3` | `uint16` | `_len` | Tamanho total do pacote (cabeçalho de 20B + payload). |
| `4..5` | `uint16` | `_checksum` | Checksum validado pelo servidor e cliente. |
| `6..7` | `int16` | `_code` | Opcode do pacote (`ePackageType`, `CrazyTankPackageType`, etc.). |
| `8..11` | `int32` | `_clientId` | Identificador único da sessão/cliente. |
| `12..15`| `int32` | `_extend1` | Campo estendido 1 (parâmetro de subsistema/sala). |
| `16..19`| `int32` | `_extend2` | Campo estendido 2 (flags de estado/canal). |
| `20..` | `bytes` | `payload` | Corpo do pacote (tipos serializados em Big-Endian). |

### 2.2. Algoritmo de Checksum (`calculateCheckSum`)

Desmontado diretamente de `PackageOut::calculateCheckSum` e `PackageIn::calculateCheckSum`:
```python
def calculate_checksum(buffer: bytes) -> int:
    chk = 119  # 0x77
    for b in buffer[6:]:  # Soma todos os bytes a partir do opcode até o final
        chk += b
    return chk & 0x7F7F  # 32639 (0x7F7F)
```

---

## 3. Cifra de Fluxo Stateful Proprietária (7Road Dynamic XOR Cipher)

O motor do DDTank utiliza uma cifra de fluxo de 8 bytes com chave mutável a cada byte transmitido, implementada em `road7th.comm.ByteSocket`:

### 3.1. Chave Inicial Padrão (`KEY`)
Desmontada de `ByteSocket::cinit` (m_id=0):
```python
DEFAULT_KEY = [0xAE, 0xBF, 0x56, 0x78, 0xAB, 0xCD, 0xEF, 0xF1]
# Decimal: [174, 191, 86, 120, 171, 205, 239, 241]
```

### 3.2. Criptografia (`ByteSocket::send`)
```python
def encrypt(data: bytes, key: list) -> bytes:
    res = bytearray(len(data))
    prev_cipher = 0
    for i in range(len(data)):
        b_plain = data[i]
        if i > 0:
            k_idx = i % 8
            key[k_idx] = ((key[k_idx] + prev_cipher) & 0xFF) ^ i
            b_cipher = ((b_plain ^ key[k_idx]) + prev_cipher) & 0xFF
        else:
            b_cipher = b_plain ^ key[0]
        prev_cipher = b_cipher
        res[i] = b_cipher
    return bytes(res)
```

### 3.3. Descriptografia (`PackageIn::loadE`)
```python
def decrypt(data: bytes, key: list) -> bytes:
    res = bytearray(len(data))
    prev_cipher = 0
    for i in range(len(data)):
        b_cipher = data[i]
        if i > 0:
            k_idx = i % 8
            key[k_idx] = ((key[k_idx] + prev_cipher) & 0xFF) ^ i
            b_plain = ((b_cipher - prev_cipher) & 0xFF) ^ key[k_idx]
        else:
            b_plain = b_cipher ^ key[0]
        prev_cipher = b_cipher
        res[i] = b_plain
    return bytes(res)
```

---

## 4. Esquema Completo de Opcodes e Protocolo (`ddt_protocol_schema.json`)

Através de [`scripts/extract_ddt_protocol_schema.py`](file:///C:/Users/dopamine/Desktop/Projetos/Reverse%20Engineering/scripts/extract_ddt_protocol_schema.py), foram extraídos **1.259 opcodes e constantes distribuídos em 32 classes** de protocolo:

### Principais Categorias:
1. **`ddt.events.CrazyTankSocketEvent` (471 constantes):**
   - Eventos de despacho no barramento interno do cliente para UI, combate, chat e inventário.
2. **`ddt.data.socket.ePackageType` (288 opcodes):**
   - Opcodes mestre de comunicação cliente-servidor:
     - `LOGIN (1)`
     - `KIT_USER (2)`
     - `SYS_MESSAGE (3)`
     - `PING (4)`
     - `SYS_DATE (5)`
     - `RSAKEY (7)` — Troca dinâmica de chave após conexão TCP.
     - `SCENE_LOGIN (16)`
     - `SCENE_ADD_USER (18)`
     - `SCENE_CHAT (19)`
     - `RECONNECT_CHANNEL (23)`
     - `LOTTERY_OPEN_BOX (26)`
3. **`ddt.data.socket.CrazyTankPackageType` (140 opcodes):**
   - Opcodes do simulador de combate em tempo real:
     - `MOVE (1)`, `FIRE (2)`, `BLAST (3)`, `TURN (6)`, `DIRECTION (7)`
     - `GUN_ROTATION (8)`, `MOVESTART (9)`, `MOVESTOP (10)`
     - `HEALTH (11)`, `SKIPNEXT (12)`, `DELAY (13)`
     - `DANDER (14)` (Fúria/Especial), `STUNT (15)`
     - `CHANGEBALL (19)`, `PROP (32)`, `FROST (33)`, `USEPROP (42)`
     - `ATTACKUP (43)`, `SHOOTSTRAIGHT (44)`, `ADDWOUND (45)`, `ADDBALL (47)`
     - `REDUCE_DANDER (242)`
4. **Sub-sistemas Adicionais Mapeados:**
   - `ConsortiaPackageType` (30 opcodes) — Sociedades/Clãs.
   - `NewChickenBoxPackageType` (26 opcodes) — Gacha de galinheiro.
   - `LittleGamePackageInType`/`OutType` (22 opcodes) — Minigames de fazenda/pesca.
   - `LabyrinthPackageType` (18 opcodes) — Modo Labirinto.
   - `WorldBossPackageType` (16 opcodes) — Chefes Globais.
   - `ChurchPackageType` (14 opcodes) — Casamentos e Salas de Cerimônia.

---

## 5. Arquitetura de Roteamento de Servidores (`ServerRouteManager`)

O arquivo revelou as rotas e fallbacks oficiais utilizados pelo client DDTank:
- **Resolução de IP de Entrada:**
  - `https://ip-api.ddclassico.com/api/ip` (Portal de roteamento regional).
  - Rotas de aceleração AWS: `aaa5935fe7a05970c.awsglobalaccelerator.com` e `aebd25ea0b4e6eb58.awsglobalaccelerator.com`.
- **Canal de Fallback Automático:**
  - `ServerRouteManager::pickFallbackChannel` seleciona dinamicamente servidores disponíveis caso o canal atual retorne timeout ou manutenção.

---

## 6. Pipeline Analítico Embarcado (`GtmService` / Google Tag Manager)

A classe `GtmService` revelou o pipeline analítico ativo em tempo real no cliente Flash:
- **Coleta de Telemetria:**
  - Envio de eventos como `player_recovery`, `days_offline`, `TrackRecoveryDays`.
  - Parâmetros rastreados: `server_id` (`Self.ZoneID`), `character_id`, `eventName`.
- **Mecanismos de Transmissão:**
  - **Bridge DOM/Electron:** Via `ExternalInterface.call("pushDataLayerGameEvent", JSON.stringify(params))`.
  - **Backend REST Fallback:** Via requisição HTTP GET para `api/gtm-event?event=...` via `URLLoader`.

---

## 7. Biblioteca Master Python Desenvolvida

Foi criada a biblioteca completa e validada [`scripts/ddt_protocol.py`](file:///C:/Users/dopamine/Desktop/Projetos/Reverse%20Engineering/scripts/ddt_protocol.py), fornecendo:
- `DDTPacket`: Serializador e deserializador com cabeçalho de 20 bytes e cálculo automático de checksum.
- `DDTStreamCipher`: Implementação exata da cifra de fluxo com chave de 8 bytes e mutação dinâmica.
- `DDTStreamReader` e `DDTStreamWriter`: Construtores de tipos primitivos ActionScript 3 (Byte, Short, Int, Long, UTF, Boolean).
- Testes automatizados cobrindo round-trip de serialização, checksum e cifragem/decifragem.
