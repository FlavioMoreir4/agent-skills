#!/usr/bin/env python3
"""Gerencia as skills deste repositório.

Comandos:
  validate [skill ...]   confere o formato (padrão aberto Agent Skills)
  install  [skill ...]   instala nas pastas que os agents leem
  package  [skill ...]   gera dist/<skill>.skill (zip) para upload no claude.ai

Sem dependências externas. Funciona em Linux, macOS e Windows (Python 3.9+).
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
DIST_DIR = ROOT / "dist"

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_NAME = 64
MAX_DESC = 1024      # limite do padrão
SOFT_DESC = 500      # alguns agents antigos truncam; mantenha abaixo disso se puder
MAX_BODY_LINES = 500
STANDARD_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
IGNORE = shutil.ignore_patterns("__pycache__", ".DS_Store", "*.pyc", ".git")

# Pastas onde os agents procuram skills (user = HOME, project = raiz do projeto).
# .claude/skills: Claude Code (e também lido por VS Code/Cursor).
# .agents/skills: Codex, Gemini CLI, Cursor, VS Code/Copilot.
TARGETS = {
    "claude": ".claude/skills",
    "agents": ".agents/skills",
}


# ---------------------------------------------------------------- frontmatter
def parse_frontmatter(text: str) -> tuple[dict[str, str] | None, str]:
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?", text, re.S)
    if not m:
        return None, text
    data: dict[str, str] = {}
    key: str | None = None
    parts: list[str] = []

    def flush() -> None:
        if key is not None:
            data[key] = " ".join(p for p in parts if p).strip().strip("\"'")

    for line in m.group(1).splitlines():
        top = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if top and not line.startswith((" ", "\t")):
            flush()
            key = top.group(1)
            rest = top.group(2).strip()
            parts = [] if rest in {">", "|", ">-", "|-", ""} else [rest]
        elif key is not None:
            parts.append(line.strip())
    flush()
    return data, text[m.end():]


# ------------------------------------------------------------------- validate
def list_skills(names: list[str]) -> list[Path]:
    if not SKILLS_DIR.is_dir():
        sys.exit(f"Pasta não encontrada: {SKILLS_DIR}")
    all_dirs = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir() and not p.name.startswith("."))
    if not names:
        return all_dirs
    by_name = {p.name: p for p in all_dirs}
    missing = [n for n in names if n not in by_name]
    if missing:
        sys.exit(f"Skill(s) inexistente(s): {', '.join(missing)}. Disponíveis: {', '.join(by_name)}")
    return [by_name[n] for n in names]


def validate_skill(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warns: list[str] = []
    skill_md = path / "SKILL.md"
    if not skill_md.is_file():
        return ["SKILL.md não encontrado (o nome do arquivo é exatamente SKILL.md)"], warns

    fm, body = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    if fm is None:
        return ["frontmatter YAML ausente (o arquivo deve começar com ---)"], warns

    name = fm.get("name", "")
    desc = fm.get("description", "")
    if not name:
        errors.append("campo 'name' ausente")
    else:
        if name != path.name:
            errors.append(f"'name' ({name}) deve ser igual ao nome da pasta ({path.name})")
        if not NAME_RE.match(name):
            errors.append("'name' só aceita minúsculas, números e hífens (sem hífen duplo, inicial ou final)")
        if len(name) > MAX_NAME:
            errors.append(f"'name' tem {len(name)} caracteres (máximo {MAX_NAME})")
    if not desc:
        errors.append("campo 'description' ausente")
    else:
        if len(desc) > MAX_DESC:
            errors.append(f"'description' tem {len(desc)} caracteres (máximo {MAX_DESC})")
        elif len(desc) > SOFT_DESC:
            warns.append(f"'description' tem {len(desc)} caracteres; abaixo de {SOFT_DESC} é mais seguro entre agents")
        if "<" in desc or ">" in desc:
            warns.append("'description' contém < ou >; evite, alguns agents tratam como marcação")

    raw = re.match(r"^---\r?\n(.*?)\r?\n---", skill_md.read_text(encoding="utf-8"), re.S)
    if raw:
        for line in raw.group(1).splitlines():
            m = re.match(r"^(name|description):\s*(.+)$", line)
            if m and m.group(2).strip() not in {">", "|", ">-", "|-"} and not m.group(2).lstrip().startswith(("'", '"')):
                if ": " in m.group(2) or " #" in m.group(2):
                    errors.append(f"'{m.group(1)}' tem ': ' ou ' #' sem aspas; parsers YAML estritos (Codex, Cursor) rejeitam. Use aspas ou bloco >")

    extra = sorted(set(fm) - STANDARD_KEYS)
    if extra:
        warns.append(f"campos fora do padrão ({', '.join(extra)}); podem ser ignorados ou quebrar em outros agents")

    if not body.strip():
        errors.append("corpo do SKILL.md vazio")
    lines = body.count("\n") + 1
    if lines > MAX_BODY_LINES:
        warns.append(f"SKILL.md tem {lines} linhas; passe detalhes para references/ (ideal até {MAX_BODY_LINES})")

    for rel in sorted(set(re.findall(r"`((?:references|scripts|assets)/[\w./-]+)`", body))):
        if not (path / rel).exists():
            errors.append(f"arquivo citado no SKILL.md não existe: {rel}")

    for p in path.rglob("*"):
        if p.is_symlink():
            warns.append(f"link simbólico dentro da skill ({p.relative_to(path)}); alguns agents ignoram")
    return errors, warns


def cmd_validate(args: argparse.Namespace) -> int:
    failed = 0
    for path in list_skills(args.skills):
        errors, warns = validate_skill(path)
        status = "ERRO" if errors else ("ok*" if warns else "ok")
        print(f"[{status}] {path.name}")
        for e in errors:
            print(f"    erro:  {e}")
        for w in warns:
            print(f"    aviso: {w}")
        failed += bool(errors)
    if failed:
        print(f"\n{failed} skill(s) com erro.")
        return 1
    print("\nTodas as skills são válidas.")
    return 0


# -------------------------------------------------------------------- install
def cmd_install(args: argparse.Namespace) -> int:
    skills = list_skills(args.skills)
    bad = [p.name for p in skills if validate_skill(p)[0]]
    if bad:
        print(f"Abortado: skills inválidas ({', '.join(bad)}). Rode 'validate'.")
        return 1

    base = Path(args.project).expanduser().resolve() if args.project else Path.home()
    keys = list(TARGETS) if args.target == "all" else [args.target]
    for key in keys:
        dest_root = base / TARGETS[key]
        for skill in skills:
            dest = dest_root / skill.name
            action = "link" if args.link else "copia"
            print(f"{action}: {skill.name} -> {dest}")
            if args.dry_run:
                continue
            dest_root.mkdir(parents=True, exist_ok=True)
            if dest.is_symlink() or dest.is_file():
                dest.unlink()
            elif dest.exists():
                shutil.rmtree(dest)
            if args.link:
                os.symlink(skill, dest, target_is_directory=True)
            else:
                shutil.copytree(skill, dest, ignore=IGNORE)
    if not args.dry_run:
        print("\nPronto. Abra uma sessão nova no agent e confira com /skills (ou equivalente).")
    return 0


# -------------------------------------------------------------------- package
def cmd_package(args: argparse.Namespace) -> int:
    skills = list_skills(args.skills)
    bad = [p.name for p in skills if validate_skill(p)[0]]
    if bad:
        print(f"Abortado: skills inválidas ({', '.join(bad)}). Rode 'validate'.")
        return 1
    DIST_DIR.mkdir(exist_ok=True)
    for skill in skills:
        out = DIST_DIR / f"{skill.name}.skill"
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in sorted(skill.rglob("*")):
                rel = f.relative_to(skill)
                if f.is_dir() or any(part in {"__pycache__", ".git", ".DS_Store"} for part in rel.parts):
                    continue
                zf.write(f, Path(skill.name) / rel)
        print(f"gerado: {out.relative_to(ROOT)}")
    return 0


# ----------------------------------------------------------------------- main
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("validate", help="valida as skills")
    p.add_argument("skills", nargs="*", help="nomes (padrão: todas)")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("install", help="instala nas pastas dos agents")
    p.add_argument("skills", nargs="*", help="nomes (padrão: todas)")
    p.add_argument("--project", metavar="DIR", help="instala no projeto DIR em vez de em ~ (escopo de usuário)")
    p.add_argument("--target", choices=["all", *TARGETS], default="all",
                   help="claude = .claude/skills; agents = .agents/skills (Codex, Gemini CLI, Cursor, Copilot); padrão: all")
    p.add_argument("--link", action="store_true",
                   help="cria link simbólico em vez de copiar (edições valem na hora; nem todo agent segue links)")
    p.add_argument("--dry-run", action="store_true", help="só mostra o que faria")
    p.set_defaults(func=cmd_install)

    p = sub.add_parser("package", help="gera dist/<skill>.skill para o claude.ai")
    p.add_argument("skills", nargs="*", help="nomes (padrão: todas)")
    p.set_defaults(func=cmd_package)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
