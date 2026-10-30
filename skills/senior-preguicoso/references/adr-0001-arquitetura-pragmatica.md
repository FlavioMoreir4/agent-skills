# ADR-0001: Arquitetura pragmática no omniaflow-plus

Copie para `docs/adr/0001-arquitetura-pragmatica.md` no repositório do plus e ajuste. Este documento tem precedência sobre os defaults da skill `senior-preguicoso`.

- **Status:** proposto (mude para "aceito" quando você revisar e concordar)
- **Data:** AAAA-MM-DD
- **Decisor:** Flavio

## Contexto

O Omniaflow (legado) cresceu com DDD e SOLID aplicados de forma muito estrita em todo o sistema. O resultado foi complexidade acima do que o domínio exige, dívida técnica acumulada e uma modelagem de banco difícil, agora com dados em produção. O projeto é mantido por uma pessoa e é a principal fonte de renda do negócio.

O omniaflow-plus existe para entregar o mesmo valor com menos complexidade. Se ele repetir a estrutura do legado, a migração terá custado tempo sem resolver o problema.

## Decisão

1. **Pragmático por padrão.** O fluxo padrão é: Controller fino → FormRequest (validação e autorização via Policy) → Action (somente quando há regra de negócio, transação ou reuso) → Eloquent → Resource/props Inertia → página Vue.
2. **CRUD simples não tem Action.** Controller + FormRequest + Eloquent.
3. **DDD tático apenas em domínios ricos**: Financeiro e Matrícula/Contrato. Nas demais áreas, não.
4. **Proibido por padrão** (exceção exige justificativa de duas linhas, registrada neste ADR ou em um novo): interface de implementação única, repository sobre Eloquent, DTO que espelha model ou request, camada que só repassa chamada, factory/strategy/manager para casos simples, evento de domínio sem listener real, novo bounded context, abstração antes da 3ª repetição, dependência nova sem necessidade concreta.
5. **Regra das três:** 1ª ocorrência escreve direto, 2ª duplica, 3ª extrai.
6. **Models Eloquent são a camada anticorrupção** sobre o schema legado enquanto ele estiver congelado. Nomes legados não vazam do model.
7. **O legado é fonte de regra de negócio, não de estilo.**
8. **Frontend:** estado local e props por padrão; componentes do shadcn-vue usados diretamente; composable na 3ª repetição; estado global só com necessidade comprovada.
9. **Orçamento de complexidade:** tarefa localizada não cria mais de 3 arquivos de produção novos sem justificativa.
10. **Dívida** é registrada em `docs/divida.md` e não é paga fora do escopo da tarefa.

## O que continua obrigatório

Autorização em toda ação, validação no servidor, isolamento entre tenants, transação e idempotência em operações financeiras e webhooks, testes dos caminhos críticos, nenhum dado real em testes ou docs.

## Consequências

- Menos arquivos e conceitos por funcionalidade, onboarding mais rápido e menos manutenção.
- Mais duplicação tolerada no curto prazo (2 ocorrências) em troca de abstrações baseadas em casos reais.
- Algumas regras de negócio ficarão em Actions e models em vez de camadas de domínio. É aceitável fora dos domínios ricos.
- Se um domínio não rico passar a ter regras que quebram dinheiro ou obrigação, reavaliar a lista no item 3.

## Como mudar esta decisão

Crie um novo ADR que a substitua, com o motivo e a evidência de produção (bug, custo, retrabalho) que justifica a mudança. Marque este como "substituído por ADR-XXXX".
