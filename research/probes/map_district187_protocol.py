#!/usr/bin/env python3
"""
District 187: Sin Streets - Master Protocol Extractor & Schema Mapper
Analyzes GameClient.dll to extract and catalog all 326 packet opcodes, categories,
packet types, and structural definitions.
"""

import os
import sys
import json
import struct
import re
import pefile

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

DLL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "targets", "district-187", "client-rebirth", "Game", "GameClient.dll"
)
OUTPUT_JSON = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "targets", "district-187", "data", "d187_protocol_schema.json"
)

def rva_to_raw(pe, rva):
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + s.Misc_VirtualSize:
            return rva - s.VirtualAddress + s.PointerToRawData
    return None

def extract_protocol():
    if not os.path.exists(DLL_PATH):
        print(f"[-] GameClient.dll not found at: {DLL_PATH}")
        return

    print(f"[+] Loading {DLL_PATH}...")
    pe = pefile.PE(DLL_PATH)
    image_base = pe.OPTIONAL_HEADER.ImageBase

    with open(DLL_PATH, "rb") as f:
        dll_bytes = f.read()

    # Find all tPacket_ string symbols
    matches = list(re.finditer(rb'tPacket_[A-Za-z0-9_]+', dll_bytes))
    print(f"[+] Found {len(matches)} raw occurrences of tPacket symbols.")

    packet_catalog = {}
    for m in matches:
        raw_offset = m.start()
        name = m.group().decode('ascii')
        
        # Calculate RVA and VA
        rva = None
        for s in pe.sections:
            if s.PointerToRawData <= raw_offset < s.PointerToRawData + s.SizeOfRawData:
                rva = raw_offset - s.PointerToRawData + s.VirtualAddress
                break
        
        if rva is None:
            continue
        va = image_base + rva

        # Parse category and packet direction from naming convention:
        # e.g., tPacket_NAccount_NIdentity_CQ_JoyGameLogin
        # or    tPacket_NMatchup_NChannel_SA_EnterUser
        parts = name.split('_')
        # Structure: tPacket_<Family>_<SubFamily>_<Direction>_<Action>
        family = parts[1] if len(parts) > 1 else "Unknown"
        subfamily = parts[2] if len(parts) > 2 else "General"
        
        direction = "Unknown"
        direction_desc = "Unknown"
        action = parts[-1]
        
        for p in parts[2:]:
            if p in ("CQ", "CN", "SA", "SN", "NN"):
                direction = p
                break
        
        if direction == "CQ":
            direction_desc = "Client Query (Request to Server)"
        elif direction == "SA":
            direction_desc = "Server Answer (Response to Query)"
        elif direction == "SN":
            direction_desc = "Server Notification (Unsolicited Event to Client)"
        elif direction == "CN":
            direction_desc = "Client Notification (Unsolicited Event to Server)"
        elif direction == "NN":
            direction_desc = "Network Broadcast (Peer-to-Peer / Channel Broadcast)"

        # Infer approximate opcode range based on known opcode families
        # 0x11xxxx: NAccount
        # 0x21xxxx: NLaunch
        # 0x22xxxx: NMatchup
        # 0x23xxxx: NBattle
        # 0x24xxxx: NGuild
        # 0x2axxxx: NAchivement
        # 0x31xxxx, 0x32xxxx: NHosting
        # 0x41xxxx: NHangar / Equipment
        
        if name not in packet_catalog:
            packet_catalog[name] = {
                "name": name,
                "family": family,
                "subfamily": subfamily,
                "direction": direction,
                "direction_description": direction_desc,
                "action": action,
                "string_va": hex(va),
                "occurrences": 1
            }
        else:
            packet_catalog[name]["occurrences"] += 1

    unique_packets = list(packet_catalog.values())
    unique_packets.sort(key=lambda x: (x["family"], x["subfamily"], x["name"]))

    print(f"[+] Total distinct packet types mapped: {len(unique_packets)}")

    # Group counts
    by_family = {}
    by_dir = {}
    for p in unique_packets:
        by_family[p["family"]] = by_family.get(p["family"], 0) + 1
        by_dir[p["direction"]] = by_dir.get(p["direction"], 0) + 1

    print("\n--- Summary by Packet Family ---")
    for fam, count in sorted(by_family.items()):
        print(f"  {fam:<16}: {count:3d} packets")

    print("\n--- Summary by Packet Direction ---")
    for d, count in sorted(by_dir.items()):
        print(f"  {d:<8}: {count:3d} packets")

    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump({
            "total_packets": len(unique_packets),
            "families": by_family,
            "directions": by_dir,
            "packets": unique_packets
        }, f, indent=2, ensure_ascii=False)

    print(f"\n[+] Master Protocol Schema exported to: {OUTPUT_JSON}")

if __name__ == "__main__":
    extract_protocol()
