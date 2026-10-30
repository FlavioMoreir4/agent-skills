# agent-skills

Repositório pessoal de skills no formato aberto [Agent Skills](https://agentskills.io): uma pasta com um `SKILL.md` (frontmatter `name` + `description`, corpo em Markdown) e arquivos de apoio opcionais. O mesmo formato funciona em Claude Code, Codex, Gemini CLI, Cursor, GitHub Copilot / VS Code e outros agents compatíveis. Aqui fica a **fonte única**; cada agent recebe uma cópia instalada.

## Skills

| Skill | Para que serve | Escopo |
|---|---|---|
| `omniaflow-migracao` | Migrar o Omniaflow (legado) para o omniaflow-plus, módulo a módulo, com o legado somente leitura | Específica do projeto |
| `senior-preguicoso` | Postura de sênior pragmático em Laravel/Inertia/Vue: solução mais simples, defaults duros, sem abstração prematura | Reutilizável |

## Estrutura

```
agent-skills/
├── skills/                  # uma pasta por skill (nome da pasta = campo name)
│   └── <skill>/
│       ├── SKILL.md         # obrigatório
│       ├── references/      # documentos lidos sob demanda
│       ├── scripts/         # código executável opcional
│       └── assets/          # templates e arquivos usados na saída
├── templates/skill/SKILL.md # ponto de partida para uma skill nova
├── scripts/skills.py        # validate | install | package (só Python 3.9+)
├── AGENTS.md                # regras para quem edita este repo (humano ou agent)
└── .github/workflows/       # CI: valida em todo push
```

## Uso

```bash
# 1. conferir o formato
python3 scripts/skills.py validate

# 2. instalar para o seu usuário (vale em todos os projetos)
python3 scripts/skills.py install                       # todas
python3 scripts/skills.py install senior-preguicoso     # só uma

# 3. ou instalar dentro de um projeto (pode ser versionado com ele)
python3 scripts/skills.py install --project ~/projetos/omniaflow-plus

# 4. gerar .skill (zip) para subir no claude.ai
python3 scripts/skills.py package
```

Opções do `install`: `--target claude|agents|all` (padrão `all`), `--link` (link simbólico em vez de cópia) e `--dry-run`. O padrão é **copiar**, porque nem todo agent segue links simbólicos. Reinstale depois de editar uma skill, ou use `--link` e confirme que seu agent enxerga a skill.

Depois de instalar, abra uma sessão nova no agent e confira com `/skills` (ou o equivalente da ferramenta). Teste de ativação: peça algo que case com a `description` e veja se a skill é carregada.

## Onde cada agent procura skills

O `install` grava em duas pastas, que juntas cobrem os agents abaixo.

| Agent | Projeto | Usuário |
|---|---|---|
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| Codex (OpenAI) | `.agents/skills/` | `~/.agents/skills/` |
| Gemini CLI | `.gemini/skills/` ou `.agents/skills/` | `~/.gemini/skills/` ou `~/.agents/skills/` |
| Cursor | `.cursor/skills/` ou `.agents/skills/` | também lê pastas de `.claude`/`.codex` |
| GitHub Copilot / VS Code | `.github/skills/`, `.claude/skills/`, `.agents/skills/` | `~/.copilot/skills/`, `~/.claude/skills/`, `~/.agents/skills/` |
| claude.ai | upload do `.skill` (zip) nas configurações de skills | — |

Essas pastas foram conferidas na documentação de cada ferramenta em outubro de 2026 e mudam com o tempo. Se um agent não achar a skill, confira o caminho na documentação dele.

## Regras de portabilidade

1. **`name` igual ao nome da pasta**, só minúsculas, números e hífens, até 64 caracteres.
2. **`description` até 1024 caracteres** (alvo: abaixo de 500). Diga o que a skill faz **e quando usar**; é o que decide se o agent a carrega.
3. **Evite `: ` e ` #` em valor sem aspas no frontmatter.** YAML estrito quebra. Use aspas ou bloco `>`. O `validate` checa isso.
4. **Só campos do padrão** no frontmatter (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`). Campos específicos de um agent (por exemplo `context: fork` do VS Code) podem ser ignorados ou quebrar nos outros.
5. **Comportamento específico de um agent fica em arquivo à parte**, nunca no corpo principal. Exemplo: `agents/openai.yaml` é lido só pelo Codex.
6. **`SKILL.md` curto** (ideal até 500 linhas). Detalhes vão para `references/`, citados com o caminho relativo (`references/x.md`) e com a instrução de quando ler.
7. **Caminhos com `/`**, relativos à pasta da skill.
8. **Sem segredos e sem dados reais** (alunos, pagamentos, tokens) em nenhum arquivo.

## Criar uma skill nova

```bash
cp -r templates/skill skills/minha-skill
# edite skills/minha-skill/SKILL.md (name = minha-skill)
python3 scripts/skills.py validate minha-skill
python3 scripts/skills.py install minha-skill
```

## Privacidade

`omniaflow-migracao` descreve decisões e convenções de um sistema em produção. Mantenha este repositório **privado**. Se quiser publicar algo, separe as skills reutilizáveis (como `senior-preguicoso`) em outro repositório.

## Referências

- Especificação: https://agentskills.io
- Codex: https://developers.openai.com/codex/skills
- Gemini CLI: https://geminicli.com/docs/cli/creating-skills/
- VS Code / Copilot: https://code.visualstudio.com/docs/agent-customization/agent-skills
- Cursor: https://cursor.com/docs/skills
