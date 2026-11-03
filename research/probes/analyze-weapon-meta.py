#!/usr/bin/env python3
"""
District 187 (S2 Online) — Weapon Meta & Balance Analysis
Analyzes damage curves, recoil, accuracy, magazine sizes and classifies weapon archetypes
using pandas.

Author: Gleidison Carvalho & Antigravity (2026-11-02)
"""
import os
import pandas as pd

CSV_PATH = r"targets\district-187\extracted\tables\WeaponInfo.csv"
OUT_REPORT = r"notes\district-187-weapon-balance-analysis.md"

def categorize_item(index):
    idx_str = str(index)
    prefix = idx_str[:3]
    categories = {
        "111": "Assault Rifle / Carbine",
        "112": "Heavy Battle Rifle (AK)",
        "113": "Shotgun",
        "114": "Sniper Rifle",
        "115": "Submachine Gun (SMG)",
        "116": "Light Machine Gun (LMG)",
        "121": "Pistol / Sidearm",
        "131": "Melee (Knife)",
        "132": "Melee (Axe)",
        "133": "Melee (Blunt / Heavy)",
        "141": "Grenade / Tactical",
    }
    return categories.get(prefix, "Special / Custom")

def analyze():
    if not os.path.exists(CSV_PATH):
        print(f"[-] CSV file not found: {CSV_PATH}")
        return

    df = pd.read_csv(CSV_PATH)
    print(f"[*] Loaded {len(df)} weapon entries from {CSV_PATH}")

    # Add Category
    df["Category"] = df["ItemIndex"].apply(categorize_item)

    # Shots to Kill (assuming standard player health = 100 HP)
    # Damage > 0
    df["STK_Body"] = df["Damage"].apply(lambda d: int((100 + d - 1) // d) if d > 0 else 0)

    # Clean up names
    df["CleanName"] = df["Name"].str.replace(r"\(Old\)", "", regex=True).str.replace(r"\(NewBase\)", "", regex=True).str.strip()

    print("\n=== Weapon Count by Category ===")
    cat_counts = df["Category"].value_counts()
    for cat, cnt in cat_counts.items():
        print(f"  {cat:<25}: {cnt:3d} weapons")

    # Generate Markdown Report
    lines = [
        "# District 187 — Análise de Balanceamento e Meta de Armas",
        "",
        "## O que foi descoberto",
        f"Análise estatística completa das **{len(df)} armas e equipamentos** de *District 187: Sin Streets*, extraídos da tabela `WeaponInfo.csv`. Mapeamos as classes de armas, curvas de dano, tiros necessários para eliminar (Shots to Kill - STK, considerando 100 HP base), capacidade de munição e controle de recuo.",
        "",
        "## Evidência e Distribuição por Classes",
        "",
        "| Categoria | Quantidade de Armas | Dano Médio | Precisão Média | Alcance Médio |",
        "|---|---|---|---|---|",
    ]

    for cat in df["Category"].unique():
        sub = df[df["Category"] == cat]
        avg_dmg = sub["Damage"].mean()
        avg_acc = sub["Accuracy"].mean()
        avg_rng = sub["Range"].mean()
        lines.append(f"| {cat} | {len(sub)} | {avg_dmg:.1f} | {avg_acc:.1f} | {avg_rng:.1f} |")

    lines.extend([
        "",
        "## Destaques Competitivos por Categoria",
        "",
        "### 1. Fuzis de Assalto e Batalha (ARs & Heavy Rifles)",
        "- **M4A1 Family:** Dano 31-34, STK = 3 a 4 tiros no tórax. Cadência ágil (`Delay` = 46), alta precisão (`Accuracy` = 52-55). A arma mais versátil do jogo.",
        "- **AK-47 Family:** Dano 34-37, STK = 3 tiros cravados no corpo (1 tiro na cabeça com multiplicador padrão de 3x). Maior recuo vertical (`Pitch` = 40) e alcance 88.",
        "- **FN-SCAR-H SE:** Dano 40, STK = 3 tiros com altíssimo alcance (80) e precisão cirúrgica (42).",
        "- **AUG A3 SE:** Dano 41, STK = 3 tiros, alcance 90 (o maior entre rifles automáticos).",
        "",
        "### 2. Snipers (Fuzis de Precisão)",
        "- **AWM-300 / DSR-E1:** Dano 100. **One-shot kill** garantido em qualquer parte do tronco superior a qualquer distância (`Range` = 100, `Accuracy` = 100).",
        "- **SVD Tiger / Argent SVD:** Dano 92 (semi-automática). STK = 2 tiros rápidos (ou 1 headshot). Alta cadência para snipers (`Delay` = 33).",
        "",
        "### 3. Submetralhadoras (SMGs)",
        "- **FN-P90:** Dano 18-19, carregador estendido de 50 projéteis (`LoadMin` = 50, `LoadMax` = 150), cadência altíssima (`Delay` = 76). Ideal para rush e combate de curta distância.",
        "- **MP5:** Dano 25-27, STK = 4 tiros, equilíbrio perfeito entre recuo baixo (`Pitch` = 31) e alcance (67).",
        "",
        "### 4. Armas Secundárias (Pistolas)",
        "- **Desert Eagle (DE Crane):** Dano 34-39. STK = 3 tiros, 6 projéteis no tambor. A pistola secundária definitiva para jogadores agressivos.",
        "- **Colt Anaconda:** Dano 31-34, maior precisão (34) e alcance (43) com recuo moderado.",
        "- **Glock:** Dano 19-25, alta cadência (`Delay` = 59) e carregador de 17 tiros.",
        "",
        "### 5. Shotguns",
        "- **Double-Barreled:** Dano 88-99 por disparo próximo. Letal à queima-roupa com capacidade de 2 cartuchos.",
        "- **Armsel Striker / AA-12:** Shotguns táticas de combate contínuo com 12 a 20 cartuchos.",
        "",
        "## Top 15 Armas de Maior Dano do Jogo",
        "",
        "| ID | Arma | Classe | Dano | STK (100 HP) | Carregador | Alcance | Precisão |",
        "|---|---|---|---|---|---|---|---|",
    ])

    top_dmg = df.sort_values(by=["Damage", "Range"], ascending=[False, False]).head(15)
    for _, row in top_dmg.iterrows():
        lines.append(f"| `{row['ItemIndex']}` | {row['Name']} | {row['Category']} | {row['Damage']} | {row['STK_Body']} | {row['LoadMin']}/{row['LoadMax']} | {row['Range']} | {row['Accuracy']} |")

    lines.extend([
        "",
        "## Aplicação no Projeto de FPS Próprio",
        "1. **Curvas de Balística:** Os dados de `Damage`, `Accuracy` (dispersão) e `Pitch` (recuo) fornecem o modelo matemático exato para calibrar o componente de tiro em Godot 4 / Unreal Engine 5.",
        "2. **Economia de Jogo:** Combinar esta tabela com `Shop.csv` e `TotalItem.csv` nos dá os preços exatos em Gold / Cash e requisitos de nível (`Level.csv`) para replicação fiel do sistema de progressão.",
        "",
        "## Próximos Passos",
        "- Cruzar os IDs `ItemIndex` com as strings de texturas em `materials/` para associar automaticamente skins às malhas extraídas.",
    ])

    os.makedirs(os.path.dirname(OUT_REPORT), exist_ok=True)
    with open(OUT_REPORT, "w", encoding="utf-8") as f_out:
        f_out.write("\n".join(lines))

    print(f"\n[+] Generated balance analysis report at {OUT_REPORT}")

if __name__ == "__main__":
    analyze()
