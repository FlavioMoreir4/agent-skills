---
name: omniaflow-migracao
description: Conduz a migração do Omniaflow (legado em produção) para o omniaflow-plus (Laravel 13, Vue, Inertia, shadcn-vue), módulo a módulo, com o legado somente leitura. Use SEMPRE que a tarefa envolver o omniaflow-plus, o legado, migrar ou portar um módulo, entender o que existe ou está quebrado no legado, coexistência entre os apps, schema compartilhado, ordem ou plano de corte, ou dívida técnica. Acione também em "como funciona X no Omniaflow?" ou "vamos fazer o módulo Y no plus".
---

# Omniaflow → omniaflow-plus

## Contexto

- **Omniaflow** (legado): ERP educacional multi-tenant em produção, com Asaas, Reverb, Horizon e Pulse. É a fonte de renda do dono. Erro financeiro ou indisponibilidade custa dinheiro real.
- **omniaflow-plus** (destino): PHP 8.5, Laravel 13, Vue + Inertia + shadcn-vue, a partir de um starter limpo. Usa **o mesmo banco** do legado, com o **schema inalterado** durante a coexistência.
- **Estratégia**: strangler por módulo. Cada módulo migrado vai para produção sozinho, atrás de roteamento por path, com rollback barato.
- **Por que migrar**: o legado ficou complexo demais (DDD/SOLID estrito), acumulou dívida técnica e tem modelagem de banco difícil. O objetivo **não** é reproduzir o legado com código novo. É entregar o comportamento que vale a pena com bem menos complexidade. Descartar o que não é usado é um resultado legítimo e esperado.

## Regras inegociáveis

Elas existem porque o custo de errar aqui é alto e quase sempre irreversível.

1. **Legado é somente leitura.** Não edite arquivos, não rode formatadores, `composer`, `artisan migrate` nem testes que escrevam estado dentro dele. Bug encontrado no legado vai para `docs/migracao/bugs-legado.md`, não é corrigido por aqui.
2. **O legado é fonte de regra de negócio, nunca de estilo.** Camadas, interfaces, nomes de classe e estrutura de pastas do legado não são convenção do plus. As convenções do plus vêm do ADR (`docs/adr/`) e da skill `senior-preguicoso`.
3. **Schema congelado.** Nenhuma migration que altere ou remova tabela ou coluna existente. As migrations do schema continuam sendo do legado até o corte. Tabela nova só com aprovação explícita do usuário e registro em `docs/migracao/`. Nunca rode `migrate`, `migrate:fresh`, `db:wipe` ou `db:seed` contra o banco de produção ou qualquer banco compartilhado. Use banco local.
4. **Dados reais ficam fora do repositório.** Nenhum dado de aluno, responsável ou pagamento em fixtures, testes, docs, logs ou prompts. Use factories com dados fictícios.
5. **Um dono por responsabilidade.** Webhook do Asaas, comando agendado, consumidor de fila e emissão de eventos Reverb têm exatamente um app responsável em cada momento. Duplicar é a causa mais provável de cobrança dupla ou job perdido.
6. **Financeiro por último e com testes de caracterização.** O formato de `externalReference` e o matching de parcelas dependem de dados que já existem no Asaas. Preserve o formato e o suporte ao legado.
7. **Um módulo por vez.** Não comece outro antes de o atual estar em produção ou ter sido pausado explicitamente pelo usuário.
8. **Não suponha, pergunte.** Se faltar informação que muda a decisão (estrutura do legado, comportamento em produção, regra de negócio ambígua), pergunte. Marque como "não verificado" o que não deu para confirmar.

## Passo 0: preparação (uma vez)

Se `docs/migracao/_indice.md` não existir:

1. Confirme o caminho do legado (padrão `../omniaflow`; veja o `AGENTS.md` (ou `CLAUDE.md`/`GEMINI.md`, conforme o agent)).
2. Mapeie a estrutura do legado com leitura localizada (`ls`, `grep`, `composer.json`, `routes/`, `app/`). Registre em `docs/migracao/_mapa-legado.md`: organização de pastas, módulos ou bounded contexts, como o tenant é resolvido, filas e schedulers, canais Reverb, integrações, versões.
3. Crie `docs/migracao/_indice.md` com a lista de módulos e, para cada um: dor, risco, frequência de mudança e status. Peça ao usuário para validar a ordem.

## Escolha do módulo

- **Baixo risco e alta dor primeiro.** Cadastros, listagens e relatórios antes de qualquer coisa que mexa com dinheiro, contrato ou matrícula.
- **O primeiro módulo é também o piloto da infraestrutura de coexistência** (sessão compartilhada, roteamento no proxy, assets, links entre apps). Escolha um pequeno e visível, para falhar barato e aprender.
- **Financeiro, cobrança Asaas e contratos ficam por último**, quando o padrão já foi validado várias vezes.

## Passo 1: análise do legado

Use o template em `references/analise-modulo.md` e gere `docs/migracao/<modulo>.md`.

Leia a partir dos pontos de entrada (rotas e páginas Vue) e desça até o banco. Não leia o legado inteiro. Para cada afirmação sobre o comportamento, cite `caminho:linha`, para que o usuário confira. Classifique cada comportamento:

- **Funciona**: faz o que deveria.
- **Quebrado**: tem defeito conhecido ou evidente.
- **Dívida**: funciona, mas é caro de manter ou entender.
- **Morto**: sem rota, sem referência ou sem uso. Confirme antes de afirmar; se o usuário puder consultar Pulse ou logs de acesso, peça.

## Passo 2: decisão (migrar, simplificar ou descartar)

Para cada comportamento relevante, registre a decisão e o motivo. Apresente ao usuário um resumo curto (até cerca de 15 linhas) e **espere a confirmação antes de escrever qualquer código no plus.** Essa pausa é o principal mecanismo contra repetir a complexidade do legado.

## Passo 3: contrato de comportamento

Defina o que precisa ficar idêntico: regras de cálculo, estados e transições, permissões, efeitos colaterais (jobs, eventos, e-mails, cache, broadcast).

- Áreas de risco (financeiro, contrato, matrícula): escreva **testes de caracterização** no plus antes de implementar. Entrada fictícia X, resultado esperado Y, conforme o legado se comporta.
- Demais áreas: testes de feature dos caminhos principais.

## Passo 4: implementação no plus

- Aplique `senior-preguicoso` em tudo que escrever.
- Use os models Eloquent como camada anticorrupção (veja `references/eloquent-anticorrupcao.md`). Nomes e formatos legados morrem dentro do model.
- Antes de **escrever** em tabela compartilhada, confirme no passo 1 quais invariantes o legado mantém (colunas derivadas, transições de status válidas, jobs e eventos disparados). Se não estiverem mapeados, mantenha o módulo somente leitura até mapear.
- Reproduza as mesmas garantias de tenancy e autorização, com teste explícito de isolamento entre tenants.
- No frontend, parta do fluxo do usuário em vez de portar tela por tela. A paridade funcional é a decidida no passo 2.

## Passo 5: paridade, corte e rollback

Siga o checklist de `references/coexistencia.md`. Em resumo:

- Roteie o módulo por path no proxy, com possibilidade de voltar para o legado só revertendo a regra de roteamento.
- Defina antes quem será o dono de cada comando agendado, fila, webhook e canal do módulo, e mude isso no mesmo deploy.
- Observe o módulo em produção por um período combinado antes de marcar o código do legado como "desligável". Não apague nada do legado nesta fase.

## Passo 6: registro

Atualize `docs/migracao/_indice.md` (status e data), registre dívida nova em `docs/divida.md` e decisões estruturais em `docs/adr/`. Termine cada resposta dizendo qual é o próximo passo.

## Depois do corte total

Só com o legado desligado, a dívida de modelagem do banco pode ser paga com mudanças em passos pequenos e reversíveis. Veja `references/expand-contract.md`. Não altere schema enquanto os dois apps escrevem no mesmo banco.

## Referências

- `references/analise-modulo.md`: template da análise por módulo.
- `references/coexistencia.md`: sessão, filas, scheduler, webhooks, Reverb, cache, storage, proxy e checklist de corte.
- `references/eloquent-anticorrupcao.md`: como esconder o schema legado atrás dos models do plus.
- `references/expand-contract.md`: evolução segura do schema depois do corte.
- `references/claude-md-sugerido.md`: bloco para o `CLAUDE.md` do plus e como proteger o legado de escrita.
