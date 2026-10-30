# Arquivo de instruções sugerido para o omniaflow-plus

Skills dependem de ser acionadas. O arquivo de instruções do projeto é lido sempre. Cole o bloco abaixo na raiz do plus e ajuste os caminhos. O conteúdo é o mesmo para qualquer agent; só muda o nome do arquivo: `AGENTS.md` (lido por Codex, Cursor, Copilot e outros), `CLAUDE.md` (Claude Code) ou `GEMINI.md` (Gemini CLI). A parte de permissões abaixo (`.claude/settings.json`) é específica do Claude Code; o clone somente leitura funciona com qualquer agent.

```markdown
# omniaflow-plus

## Contexto
Reescrita incremental do Omniaflow (legado em produção) para PHP 8.5 / Laravel 13 /
Vue + Inertia + shadcn-vue. Mesmo banco do legado; schema inalterado até o corte.

## Legado (somente leitura)
- Caminho: ../omniaflow-ref
- NUNCA editar, formatar, rodar composer/artisan/testes que escrevam estado ou migrations ali.
- O legado é fonte de regra de negócio, não de estilo.

## Banco
- NUNCA rodar migrate, migrate:fresh, db:wipe ou db:seed contra produção ou banco compartilhado.
- Desenvolvimento usa banco local com schema do legado e dados fictícios.
- Nenhum dado real de aluno, responsável ou pagamento em código, testes, docs ou logs.

## Como trabalhar
- Migração de módulo: skill `omniaflow-migracao` (um módulo por vez; confirmar a decisão antes de implementar).
- Qualquer código novo: skill `senior-preguicoso` e `docs/adr/0001-arquitetura-pragmatica.md`.
- Módulos de domínio rico (DDD tático permitido): Financeiro, Matrícula/Contrato.
- Dívida nova: registrar em docs/divida.md. Não refatorar fora do escopo da tarefa.
```

## Acesso de consulta ao legado

Opção 1, em uma sessão do Claude Code dentro do plus:

```bash
cd ~/projetos/omniaflow-plus
claude --add-dir ../omniaflow-ref
```

Em uma sessão já aberta: `/add-dir ../omniaflow-ref`.

## Como proteger o legado de escrita (do mais fraco ao mais forte)

1. **Regra no `CLAUDE.md` e na skill.** Orienta o comportamento, mas não impede nada tecnicamente.
2. **Regras de permissão no `.claude/settings.json`** negando edição no caminho do legado. A sintaxe do padrão de caminho varia entre versões, então confira com `/permissions` e teste. Exemplo de forma geral:

   ```json
   {
     "permissions": {
       "deny": [
         "Edit(../omniaflow-ref/**)",
         "Write(../omniaflow-ref/**)"
       ]
     }
   }
   ```

   Limitação: isso cobre as ferramentas de edição, **não** comandos de shell que escrevem em arquivos (por exemplo `sed -i`). Por isso não basta sozinho.
3. **Cópia de referência somente leitura (recomendada).** Em vez de apontar para o repositório em que você trabalha, crie um clone ou worktree dedicado à consulta e tire a permissão de escrita no sistema de arquivos:

   ```bash
   git clone git@github.com:SEU_USUARIO/omniaflow.git ../omniaflow-ref
   chmod -R a-w ../omniaflow-ref
   ```

   Para atualizar a cópia: `chmod -R u+w ../omniaflow-ref && git -C ../omniaflow-ref pull && chmod -R a-w ../omniaflow-ref`.
   Isso impede escrita por qualquer caminho, inclusive shell, e não atrapalha o seu repositório de trabalho do legado.

Não coloque no clone de referência o `.env` nem credenciais de produção. Para consulta de código eles não são necessários.
