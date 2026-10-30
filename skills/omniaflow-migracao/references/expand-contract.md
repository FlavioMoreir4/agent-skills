# Evolução do schema depois do corte (expand/contract)

**Pré-condição:** o legado está desligado, ou seja, só o omniaflow-plus escreve no banco. Mudar schema com dois apps escrevendo é o cenário mais perigoso de toda a migração. Se a pré-condição não vale, não use este documento.

A ideia é nunca fazer uma mudança que não possa ser desfeita em um passo. Cada etapa é um deploy separado, com tempo de observação entre elas.

## Sequência

1. **Expandir.** Adicione a estrutura nova sem remover nada: coluna nova (nullable ou com default seguro), tabela nova, índice novo. O código atual continua funcionando.
2. **Escrever nos dois.** O app grava no formato antigo e no novo. A leitura continua no antigo.
3. **Backfill.** Preencha o novo a partir do antigo para os dados históricos, em lotes, de forma idempotente e com ponto de retomada. Rode fora do horário de pico.
4. **Verificar.** Compare contagens, somas e amostras entre antigo e novo. Para financeiro, concilie valores. Registre o resultado.
5. **Migrar leituras.** Passe a ler do novo. Mantenha a escrita nos dois por um período.
6. **Observar.** Período combinado sem divergência.
7. **Contrair.** Pare de escrever no antigo e, em deploy posterior, remova a estrutura antiga.

Cada passo tem rollback: voltar a leitura para o antigo (passo 5), parar a escrita no novo (passos 2 e 3) ou restaurar o backup (passo 7).

## Regras

- **Backup recente e restauração testada** antes de qualquer etapa destrutiva.
- Ensaie tudo em uma cópia dos dados de produção, em ambiente isolado e sem PII exposta.
- Nunca altere valores financeiros históricos. Corrija por lançamento novo, com rastreabilidade.
- Mudanças em tabelas grandes podem travar escrita. Conforme o SGBD, use algoritmos online (`ALGORITHM=INPLACE`/`INSTANT` no MySQL, `CREATE INDEX CONCURRENTLY` no PostgreSQL) ou ferramentas como gh-ost e pt-online-schema-change.
- Backfill em lotes pequenos, com `chunkById`, sem transação gigante, com log de progresso.
- Uma mudança de schema por vez. Não combine renomear, mudar tipo e mover dados no mesmo deploy.
- Não renomeie coluna "direto". Crie a nova, migre, remova a antiga.
- Registre cada mudança em `docs/adr/` ou em `docs/migracao/schema.md`, com data, motivo e plano de rollback.

## Ordem sugerida

Comece pelas correções que mais reduzem complexidade no código do plus, as que fizeram o model ficar "mentiroso" (veja `eloquent-anticorrupcao.md`). Financeiro e matching de parcelas ficam por último e com conciliação em cada passo.
