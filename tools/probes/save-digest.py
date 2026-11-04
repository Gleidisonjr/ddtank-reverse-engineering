"""
save-digest.py — Cola o output do Claude (extensão Chrome) e salva em notes/digest-YYYY-MM-DD.md
Uso: python scripts/save-digest.py
     (cole o conteúdo quando solicitado, finalize com Ctrl+Z no Windows)
  ou: python scripts/save-digest.py < conteudo.txt
"""

import sys
from datetime import date
from pathlib import Path

NOTES_DIR = Path(__file__).parent.parent / "notes"
NOTES_DIR.mkdir(exist_ok=True)


def main():
    today = date.today().isoformat()
    output_path = NOTES_DIR / f"digest-{today}.md"

    if sys.stdin.isatty():
        print("Cole o output do Claude abaixo.")
        print("Finalize com Ctrl+Z (Windows) ou Ctrl+D (Linux/Mac) + Enter:\n")

    content = sys.stdin.read().strip()

    if not content:
        print("Nenhum conteúdo recebido. Saindo.")
        sys.exit(1)

    header = f"# Feed Digest — {today}\n\n"

    if output_path.exists():
        with open(output_path, "a", encoding="utf-8") as f:
            f.write(f"\n\n---\n\n{content}\n")
        print(f"Adicionado ao existente: {output_path}")
    else:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(header + content + "\n")
        print(f"Criado: {output_path}")

    print(f"\nPróximo passo: abra o Claude Code e diga 'analisa o digest de hoje'")


if __name__ == "__main__":
    main()
