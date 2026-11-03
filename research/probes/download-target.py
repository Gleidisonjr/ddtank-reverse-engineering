#!/usr/bin/env python3
"""
download-target.py — Download seguro e cálculo de hash para arquivos de alvos de RE
Objetivo: Baixar S2.rar da URL fornecida, calcular SHA256 e MD5 em streaming.
"""

import sys
import hashlib
from pathlib import Path
import httpx

TARGET_DIR = Path(__file__).resolve().parent.parent / "targets" / "district-187" / "downloads"
TARGET_DIR.mkdir(parents=True, exist_ok=True)
DEST_FILE = TARGET_DIR / "S2.rar"

URL = "https://drive.usercontent.google.com/download?id=1FJiWk1Lvu3UUvboQfYH1q6UVotx5aQW4&export=download&authuser=0&confirm=t"


def main():
    if DEST_FILE.exists() and DEST_FILE.stat().st_size > 1000000000:
        print(f"[*] Arquivo já existe: {DEST_FILE} ({DEST_FILE.stat().st_size:,} bytes)")
        sha256 = hashlib.sha256()
        with open(DEST_FILE, "rb") as f:
            while chunk := f.read(1024 * 1024):
                sha256.update(chunk)
        print(f"[OK] SHA-256: {sha256.hexdigest()}")
        return

    print(f"[*] Conectando para download de {DEST_FILE.name}...")
    sha256 = hashlib.sha256()
    md5 = hashlib.md5()
    downloaded = 0

    with httpx.stream("GET", URL, follow_redirects=True, timeout=60.0) as resp:
        if resp.status_code != 200:
            print(f"[!] Erro HTTP {resp.status_code}", file=sys.stderr)
            sys.exit(1)

        total = int(resp.headers.get("content-length", 0))
        print(f"[*] Tamanho total: {total / (1024*1024):.2f} MB")

        last_percent = -1
        with open(DEST_FILE, "wb") as f:
            for chunk in resp.iter_bytes(chunk_size=1024 * 1024):
                f.write(chunk)
                sha256.update(chunk)
                md5.update(chunk)
                downloaded += len(chunk)
                if total > 0:
                    pct = int(downloaded / total * 100)
                    if pct != last_percent and pct % 10 == 0:
                        print(f"[*] Progresso: {pct}% ({downloaded / (1024*1024):.1f} MB / {total / (1024*1024):.1f} MB)")
                        last_percent = pct

    print(f"\n[OK] Download concluído com sucesso!")
    print(f"  Tamanho: {DEST_FILE.stat().st_size:,} bytes")
    print(f"  SHA-256: {sha256.hexdigest()}")
    print(f"  MD5:     {md5.hexdigest()}")


if __name__ == "__main__":
    main()
