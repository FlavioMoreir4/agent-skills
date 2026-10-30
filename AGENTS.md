# Instruções para quem edita este repositório

Este repositório guarda skills no formato aberto Agent Skills. Ele é lido por qualquer agent; as regras abaixo valem para todos.

## Estrutura e regras

- Cada skill é uma pasta em `skills/<nome>/` com um `SKILL.md`. O campo `name` do frontmatter é igual ao nome da pasta.
- Só campos padrão no frontmatter: `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`.
- `description`: até 1024 caracteres, alvo abaixo de 500, dizendo o que a skill faz e **quando usar**. Sem `: ` nem ` #` em valor sem aspas.
- `SKILL.md` com até 500 linhas. Detalhes vão para `references/`, e o `SKILL.md` diz quando ler cada arquivo.
- Instruções específicas de um agent ficam em arquivos separados e nunca no corpo principal.
- Nunca commitar segredos, tokens ou dados reais de alunos, responsáveis ou pagamentos.

## Fluxo de trabalho

1. Edite a skill.
2. Rode `python3 scripts/skills.py validate`. Corrija todo erro; avisos são decisão sua.
3. Reinstale com `python3 scripts/skills.py install <skill>` se quiser testar.
4. Não crie arquivos, pastas ou scripts além do necessário. Prefira editar o que existe.

## Estilo das skills

Escreva em português, no imperativo, explicando o porquê das regras em vez de empilhar proibições. Prefira defaults claros a princípios vagos. Não repita a mesma regra em várias seções.
