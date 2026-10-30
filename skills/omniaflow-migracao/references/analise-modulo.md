# Template: análise de módulo do legado

Copie para `docs/migracao/<modulo>.md` e preencha. Toda afirmação sobre comportamento cita `caminho:linha`. O que não foi possível confirmar vai como **não verificado**.

```markdown
# Módulo: <nome>

- Status: análise | decidido | em implementação | em produção no plus | legado desligável
- Data da análise: AAAA-MM-DD
- Risco (baixo/médio/alto) e por quê:
- Frequência de mudança (quanto você mexe aqui):
- Dor atual (o que incomoda no legado):

## 1. Pontos de entrada
| Tipo | Identificador | Local | Observação |
|---|---|---|---|
| Rota | GET /... | routes/web.php:NN | middleware, policy |
| Página Vue | Pages/.../X.vue | caminho | |
| Comando agendado | comando:nome | app/Console/... | frequência |
| Job / Listener | NomeJob | caminho | fila usada |
| Webhook / integração | Asaas evento X | caminho | |
| Canal Reverb | nome do canal | caminho | quem emite, quem escuta |

## 2. Regras de negócio
Para cada regra: descrição curta, local no código, classificação e decisão.

| # | Regra | Local | Classificação | Decisão | Motivo |
|---|---|---|---|---|---|
| 1 | | caminho:linha | funciona / quebrado / dívida / morto | migrar / simplificar / descartar | |

## 3. Dados
| Tabela | Colunas usadas | Leitura/Escrita | Invariantes mantidas pelo legado |
|---|---|---|---|
| | | | colunas derivadas, status válidos, efeitos colaterais |

- Colunas ou valores "mágicos" (flags, códigos, enums implícitos):
- Relações implícitas (sem FK no banco):
- Quem mais escreve nessas tabelas (outros módulos, jobs, webhooks):

## 4. Autorização e tenancy
- Permissões, policies e papéis envolvidos:
- Como o tenant é aplicado (global scope, middleware, coluna, conexão):
- Pontos onde o isolamento depende de convenção e não de mecanismo:

## 5. Efeitos colaterais
E-mails, notificações, cache, broadcast, arquivos gerados, chamadas externas.

## 6. Testes existentes
O que existe, o que cobre, o que é confiável.

## 7. Bugs e riscos encontrados no legado
Lista com local e impacto. Não corrigir no legado; registrar em `docs/migracao/bugs-legado.md`.

## 8. Decisão resumida (para o usuário confirmar)
- Migrar: ...
- Simplificar: ...
- Descartar: ...
- Dependências de outros módulos:
- Estimativa de esforço e o que fica de fora desta etapa:

## 9. Contrato de comportamento
Lista do que precisa ficar idêntico e quais testes de caracterização cobrem cada item.

## 10. Plano de corte
- Roteamento (paths que passam para o plus):
- Donos novos (scheduler, filas, webhook, canais):
- Rollback:
- Período de observação e critério para marcar o legado como desligável:
```
