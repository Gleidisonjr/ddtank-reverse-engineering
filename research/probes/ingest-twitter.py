#!/usr/bin/env python3
"""
ingest-twitter.py — Pipeline de ingestão e processamento do feed técnico do Twitter/X
Objetivo: Ingerir tweets e descobertas técnicas, atualizar o digest diário no Obsidian
          e gerar notas atômicas interligadas para ferramentas e repositórios relevantes.

Input esperado:
  - Clipboard do Windows (--clipboard) contendo texto copiado do Twitter / Claude no Chrome
  - Arquivo texto/markdown (--file caminho.txt)
  - Entrada padrão / stdin (pipe ou digitação com Ctrl+Z)
  - Teste sintético (--test)

Output gerado:
  - notes/digest-YYYY-MM-DD.md (Digest diário consolidado com wikilinks Obsidian)
  - notes/<slug>.md (Notas atômicas para itens técnicos com repositório/ferramenta)
  - Home.md (Atualizado com links para as novas notas atômicas no vault)

Uso:
  python scripts/ingest-twitter.py --clipboard
  python scripts/ingest-twitter.py --file raw-feed.txt
  python scripts/ingest-twitter.py --test
  python scripts/ingest-twitter.py --help
"""

import os
import re
import sys
import argparse
import subprocess
from datetime import date
from pathlib import Path
from typing import List, Dict, Optional, Tuple

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_DIR = Path(__file__).resolve().parent.parent
NOTES_DIR = PROJECT_DIR / "notes"
HOME_FILE = PROJECT_DIR / "Home.md"

NOTES_DIR.mkdir(exist_ok=True)

# Categorias elegíveis para gerar notas atômicas automáticas quando tiverem repo/alta relevância
ATOMIC_NOTE_CATEGORIES = {"FERRAMENTA", "FRAMEWORK", "REPOSITÓRIO", "BIBLIOTECA"}


def get_clipboard_text() -> str:
    """Lê o conteúdo textual da área de transferência do Windows via PowerShell."""
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        return proc.stdout.strip()
    except Exception as exc:
        print(f"[!] Erro ao acessar clipboard: {exc}", file=sys.stderr)
        return ""


def slugify(text: str) -> str:
    """Gera um slug compatível com as notas do Second Brain (lowercase-with-hyphens)."""
    text = re.sub(r"\([^)]*\)", "", text)  # remove parênteses e conteúdo (ex: (Microsoft))
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text).strip("-")
    return text or "nota-tecnica"


def extract_github_url(text: str) -> Optional[str]:
    """Extrai URL do GitHub do texto se presente."""
    match = re.search(r"https?://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", text)
    if match:
        return match.group(0).rstrip(".")
    # Caso simplificado: github.com/owner/repo ou owner/repo
    match_simple = re.search(r"(?:GitHub:\s*|github\.com/)([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)", text)
    if match_simple:
        return f"https://github.com/{match_simple.group(1).rstrip('.')}"
    return None


def parse_digest_text(content: str) -> List[Dict]:
    """
    Analisa o texto de entrada e extrai itens estruturados.
    Suporta formato padronizado (**[CATEGORIA]** Título) e blocos semi-estruturados.
    """
    items = []
    # Regex para capturar itens formatados como: **[CATEGORIA]** Título
    pattern = r"\*\*\[([A-ZÁÉÍÓÚÂÊÔÃÕÇa-z0-9_-]+)\]\*\*\s*([^\n]+)"
    matches = list(re.finditer(pattern, content))

    if matches:
        for i, match in enumerate(matches):
            category = match.group(1).strip().upper()
            title = match.group(2).strip()
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            body = content[start_pos:end_pos].strip()

            what_is = ""
            why_it_matters = ""
            link = ""
            note_link = ""
            github_url = extract_github_url(body) or extract_github_url(title)

            for line in body.splitlines():
                line_str = line.strip()
                if line_str.startswith("→ O que é:") or line_str.startswith("- O que é:"):
                    what_is = re.sub(r"^[→-]\s*O que é:\s*", "", line_str).strip()
                elif line_str.startswith("→ Por que importa:") or line_str.startswith("- Por que importa:"):
                    why_it_matters = re.sub(r"^[→-]\s*Por que importa:\s*", "", line_str).strip()
                elif line_str.startswith("→ Link:") or line_str.startswith("- Link:"):
                    link = re.sub(r"^[→-]\s*Link:\s*", "", line_str).strip()
                elif line_str.startswith("→ Fonte:") or line_str.startswith("- Fonte:"):
                    if not link:
                        link = re.sub(r"^[→-]\s*Fonte:\s*", "", line_str).strip()
                elif line_str.startswith("→ Nota:") or line_str.startswith("- Nota:"):
                    note_link = re.sub(r"^[→-]\s*Nota:\s*", "", line_str).strip()

            items.append({
                "category": category,
                "title": title,
                "body": body,
                "what_is": what_is,
                "why_it_matters": why_it_matters,
                "link": link,
                "github_url": github_url,
                "note_link": note_link,
            })
    else:
        # Fallback: divide por blocos ou tweets individuais separados por linhas em branco duplas
        blocks = [b.strip() for b in re.split(r"\n\s*\n", content) if b.strip()]
        for idx, block in enumerate(blocks):
            lines = [l.strip() for l in block.splitlines() if l.strip()]
            if not lines:
                continue
            first_line = lines[0]
            title = first_line[:80] + ("..." if len(first_line) > 80 else "")
            github_url = extract_github_url(block)
            category = "REPOSITÓRIO" if github_url else "DESCOBERTA"

            items.append({
                "category": category,
                "title": title,
                "body": block,
                "what_is": block,
                "why_it_matters": "",
                "link": "",
                "github_url": github_url,
                "note_link": "",
            })

    return items


def create_atomic_note(item: Dict, today_str: str) -> Optional[Tuple[str, Path]]:
    """
    Cria uma nota atômica para uma ferramenta/repositório caso ainda não exista.
    Retorna o slug e o path do arquivo criado, ou None se já existir.
    """
    title = item["title"]
    # Limpa o título para gerar slug
    main_title = title.split("—")[0].split("-")[0].strip()
    slug = slugify(main_title)
    note_path = NOTES_DIR / f"{slug}.md"

    if note_path.exists():
        return slug, note_path

    repo_line = f"**Repositório:** {item['github_url']}\n" if item["github_url"] else ""
    what_is = item["what_is"] or item["title"]
    why_it_matters = item["why_it_matters"] or "Descoberta técnica no feed técnico do Twitter/X para o Second Brain."

    content = f"""# {main_title}

{repo_line}**Descoberto:** {today_str} via [[notes/digest-{today_str}]]
**Categoria:** {item['category']}

## O que é

{what_is}

## Detalhes / Funcionamento

{item['body']}

## Relevância para o projeto

{why_it_matters}

## Próximos passos

- [ ] Avaliar aplicabilidade no projeto de Engenharia Reversa e pipelines
- [ ] Testar no ambiente local se aplicável
"""
    with open(note_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"  [+] Nota atômica criada: notes/{slug}.md")
    return slug, note_path


def update_home_index(new_notes: List[Tuple[str, str]]):
    """Adiciona as novas notas atômicas criadas à lista de descobertas no Home.md."""
    if not HOME_FILE.exists() or not new_notes:
        return

    try:
        content = HOME_FILE.read_text(encoding="utf-8")
        marker = "### Notas de descoberta"
        if marker not in content:
            return

        added_lines = []
        for slug, title in new_notes:
            link_entry = f"[[notes/{slug}]]"
            if link_entry not in content:
                added_lines.append(f"→ [[notes/{slug}]] — {title}")

        if not added_lines:
            return

        insertion = "\n".join(added_lines) + "\n"
        idx = content.find(marker) + len(marker)
        updated_content = content[:idx] + "\n" + insertion + content[idx + 1:]

        HOME_FILE.write_text(updated_content, encoding="utf-8")
        print(f"  [+] Home.md atualizado com {len(added_lines)} nova(s) referência(s).")
    except Exception as exc:
        print(f"  [!] Aviso: Não foi possível atualizar Home.md: {exc}", file=sys.stderr)


def process_feed(content: str, create_notes: bool = True) -> int:
    """Processa o feed bruto e gera o digest e notas atômicas."""
    today_str = date.today().isoformat()
    digest_path = NOTES_DIR / f"digest-{today_str}.md"

    items = parse_digest_text(content)
    if not items:
        print("[!] Nenhum item identificado no conteúdo.")
        return 0

    print(f"[*] {len(items)} itens identificados para o digest de {today_str}.")

    new_atomic_notes: List[Tuple[str, str]] = []

    # Se create_notes for True, cria notas atômicas para ferramentas/repositórios
    for item in items:
        should_make_note = (
            create_notes and
            (item["category"] in ATOMIC_NOTE_CATEGORIES or item["github_url"]) and
            not item["note_link"]
        )
        if should_make_note:
            res = create_atomic_note(item, today_str)
            if res:
                slug, _ = res
                item["note_link"] = f"[[notes/{slug}]]"
                new_atomic_notes.append((slug, item["title"]))

    # Monta o texto dos itens para o digest
    digest_blocks = []
    for item in items:
        lines = [f"**[{item['category']}]** {item['title']}"]
        if item["what_is"]:
            lines.append(f"→ O que é: {item['what_is']}")
        elif item["body"]:
            first_body = item["body"].split("\n")[0]
            lines.append(f"→ Detalhes: {first_body}")

        if item["note_link"]:
            lines.append(f"→ Nota: {item['note_link']}")
        if item["why_it_matters"]:
            lines.append(f"→ Por que importa: {item['why_it_matters']}")
        if item["github_url"]:
            lines.append(f"→ GitHub: {item['github_url']}")
        if item["link"]:
            lines.append(f"→ Link: {item['link']}")

        digest_blocks.append("\n".join(lines))

    formatted_items = "\n\n".join(digest_blocks)

    # Escreve ou adiciona ao digest do dia
    if digest_path.exists():
        with open(digest_path, "a", encoding="utf-8") as f:
            f.write(f"\n\n---\n\n{formatted_items}\n")
        print(f"  [+] Itens adicionados ao digest existente: {digest_path.name}")
    else:
        header = f"# Feed Digest — {today_str}\n\n> {len(items)} itens técnicos filtrados e processados\n\n---\n\n"
        with open(digest_path, "w", encoding="utf-8") as f:
            f.write(header + formatted_items + "\n")
        print(f"  [+] Novo digest criado: {digest_path.name}")

    if new_atomic_notes:
        update_home_index(new_atomic_notes)

    print(f"\n[OK] Ingestão concluída com sucesso! ({len(items)} itens, {len(new_atomic_notes)} notas atômicas)")
    return len(items)


SAMPLE_INPUT = """\
**[FERRAMENTA]** FastGraph — Visualizador interativo de grafos para chamadas RE
→ O que é: Ferramenta em Rust e WebAssembly para renderizar fluxogramas de controle e grafos de chamadas interativos a partir de dumps do Ghidra e REA.
→ GitHub: https://github.com/fastgraph/fastgraph
→ Link: x.com/fastgraph_dev/status/2117123456789012345 · @fastgraph_dev
→ Por que importa: Acelera em 3x a navegação visual de rotas complexas sem abrir a GUI pesada do Ghidra.

**[FRAMEWORK]** AgentForge — Multi-agent evaluation harness
→ O que é: Framework de teste adversarial e validação estatística de respostas geradas por agentes autônomos.
→ GitHub: https://github.com/agentforge-ai/agentforge
→ Link: x.com/agentforge/status/2117987654321098765
→ Por que importa: Permite mensurar taxas de drift e alucinações em loops contínuos de código.
"""


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline de ingestão técnica do Twitter/X para o Second Brain (Obsidian)"
    )
    parser.add_argument("--clipboard", "-c", action="store_true",
                        help="Ler conteúdo da área de transferência do Windows")
    parser.add_argument("--file", "-f", type=Path,
                        help="Caminho do arquivo com os dados extraídos")
    parser.add_argument("--test", "-t", action="store_true",
                        help="Executar com dados de exemplo para validação")
    parser.add_argument("--no-atomic", action="store_true",
                        help="Não gerar notas atômicas separadas para repositórios")

    args = parser.parse_args()

    content = ""
    if args.test:
        print("[*] Modo de teste ativado. Usando payload de exemplo.")
        content = SAMPLE_INPUT
    elif args.file:
        if not args.file.exists():
            print(f"[!] Arquivo não encontrado: {args.file}", file=sys.stderr)
            sys.exit(1)
        content = args.file.read_text(encoding="utf-8").strip()
    elif args.clipboard:
        print("[*] Lendo conteúdo da área de transferência...")
        content = get_clipboard_text()
        if not content:
            print("[!] Clipboard vazio ou sem texto detectado.", file=sys.stderr)
            sys.exit(1)
    else:
        # Stdin
        if sys.stdin.isatty():
            print("Cole o conteúdo do feed abaixo (finalize com Ctrl+Z no Windows ou Ctrl+D no Linux + Enter):\n")
        content = sys.stdin.read().strip()

    if not content:
        print("[!] Nenhum conteúdo fornecido. Use --clipboard, --file, ou cole na entrada padrão.", file=sys.stderr)
        sys.exit(1)

    create_notes = not args.no_atomic
    process_feed(content, create_notes=create_notes)


if __name__ == "__main__":
    main()
