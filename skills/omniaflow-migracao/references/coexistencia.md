# Coexistência entre Omniaflow e omniaflow-plus

Enquanto os dois apps vivem lado a lado no mesmo banco, os problemas aparecem nas **fronteiras compartilhadas**. Cada seção abaixo é uma dessas fronteiras. Valide tudo em staging com uma cópia do ambiente antes de produção.

## Sumário
1. Roteamento
2. Sessão e autenticação
3. Filas e Horizon
4. Scheduler
5. Webhooks do Asaas
6. Reverb e broadcasting
7. Cache
8. Storage de arquivos
9. Tenancy
10. Migrations e schema local
11. Checklist de corte

## 1. Roteamento

Um proxy (Nginx ou equivalente) na frente decide por path qual app atende. Migrar um módulo é adicionar o path dele ao plus. Reverter é remover a regra.

```nginx
# esquema: paths migrados vão para o plus, o resto continua no legado
location ^~ /modulo-migrado { proxy_pass http://omniaflow_plus; }
location /                  { proxy_pass http://omniaflow_legado; }
```

Detalhes que costumam morder:

- **Links entre os apps devem ser navegação completa** (`<a href>`), nunca `<Link>` do Inertia. Uma visita Inertia para uma URL servida por outro app recebe resposta que não é Inertia e quebra a experiência.
- Cada app tem seus próprios assets e versão de assets. Não compartilhe o diretório de build.
- Mantenha os mesmos hosts e subdomínios dos tenants nos dois apps.
- Prefira rotas agrupadas por módulo (prefixo), para a regra do proxy ser simples.

## 2. Sessão e autenticação

Para o usuário não ser deslogado ao trocar de módulo, os dois apps precisam concordar em:

- mesma `APP_KEY` (a sessão e os cookies são criptografados com ela);
- mesmo `SESSION_DRIVER` e mesma conexão e tabela de sessão;
- mesmo `SESSION_COOKIE` e `SESSION_DOMAIN`;
- mesma tabela de usuários e mesma coluna de senha, com o mesmo algoritmo de hash;
- mesma configuração de `SESSION_SECURE_COOKIE` e `SAME_SITE`.

Teste login nos dois sentidos: logar no legado e abrir página do plus, e o inverso. Teste também logout e expiração. Se algum dos dois usa middleware que invalida sessão por troca de senha (por exemplo `AuthenticateSession`), valide que o hash armazenado é compatível.

## 3. Filas e Horizon

Um job serializado pelo legado referencia classes que o plus não tem (e vice-versa). Um worker do app errado que pegue esse job falha.

- Separe as filas por app (nomes distintos) e, se usar Redis, use prefixos diferentes para as filas e para o Horizon.
- Cada app só processa jobs que ele mesmo conhece.
- Se um app precisa disparar trabalho no outro, prefira um mecanismo desacoplado (chamada HTTP interna, ou um registro em tabela que o outro consome) em vez de enfileirar classes do outro.
- Ao migrar um módulo, os jobs dele passam a ser despachados pelo plus. Antes de desligar o consumidor do legado, **esvazie a fila antiga** daquele módulo.

## 4. Scheduler

Se o mesmo comando agendado rodar nos dois apps, ele executa duas vezes.

- Cada comando tem exatamente um dono. Registre o dono em `docs/migracao/_indice.md`.
- Ao migrar, desligue no legado e ligue no plus **no mesmo deploy**. Se o comando é idempotente, é aceitável ligar no novo antes de desligar no antigo; se não é, desligue primeiro e aceite uma janela sem execução.
- Comandos que mexem com dinheiro (cobrança, geração de parcelas, conciliação) nunca rodam nos dois ao mesmo tempo.

## 5. Webhooks do Asaas

- A URL de webhook cadastrada no Asaas é uma só por vez. Um app é o dono e processa o evento.
- Valide sempre o token de autenticação configurado no webhook.
- Processe de forma **idempotente**: o Asaas pode reenviar eventos. Use a identidade do evento ou do pagamento mais o tipo para ignorar repetições.
- Se o plus passa a ser dono do webhook enquanto o legado ainda depende de algum efeito, o dono encaminha internamente. Não cadastre duas URLs que processem o mesmo evento.
- Preserve o formato de `externalReference` e o suporte ao legado no matching de parcelas. Cobranças antigas continuam existindo no Asaas.

## 6. Reverb e broadcasting

- Os dois apps podem usar o mesmo servidor Reverb (mesmos `REVERB_APP_ID`, key e secret) para publicar.
- Defina qual app emite cada canal. Dois apps emitindo o mesmo evento para o mesmo canal geram eventos duplicados no cliente.
- A autenticação de canais privados (`/broadcasting/auth`) deve ser servida pelo app que renderiza a página que se conecta ao canal.
- Os nomes de evento e o formato do payload são contrato com o frontend. Se a tela migra, o contrato muda junto.

## 7. Cache

- Use `CACHE_PREFIX` diferente em cada app para evitar colisão, exceto chaves compartilhadas de propósito (documente-as).
- Não compartilhe objetos serializados de classes que só um dos apps conhece. Compartilhe apenas valores simples (arrays, strings, números).

## 8. Storage de arquivos

- Os dois apps apontam para o mesmo disk e usam a mesma convenção de caminhos para os arquivos existentes.
- Quem grava um tipo de arquivo define a convenção. O outro só lê, até o corte.
- URLs assinadas e permissões de acesso precisam ser equivalentes nos dois apps.

## 9. Tenancy

- A resolução do tenant (domínio, subdomínio, header, sessão) deve produzir o mesmo tenant nos dois apps.
- Escreva um teste explícito de isolamento no plus: usuário do tenant A não lê nem altera dados do tenant B, em consulta, job, broadcast e arquivo.
- Cuidado com jobs e comandos que rodam sem request: eles precisam definir o tenant explicitamente.

## 10. Migrations e schema local

- O legado é dono das migrations do schema até o corte. O plus **não** roda migrations contra o banco compartilhado.
- Para desenvolver o plus, monte um banco local a partir de um dump **somente do schema** do banco do legado (`mysqldump --no-data` ou `pg_dump --schema-only`, conforme o SGBD) e popule com factories fictícias.
- Não use `php artisan schema:dump` dentro do repositório legado, porque ele escreve arquivos nele.

## 11. Checklist de corte de um módulo

**Antes**
- [ ] Análise do módulo concluída e decisões confirmadas pelo usuário
- [ ] Testes de caracterização (áreas de risco) ou de feature passando
- [ ] Teste de isolamento entre tenants passando
- [ ] Permissões e policies equivalentes às do legado
- [ ] Jobs, eventos, e-mails e broadcasts do módulo mapeados e com dono definido
- [ ] Sessão validada nos dois sentidos em staging
- [ ] Plano de rollback escrito (reverter a regra do proxy e devolver donos)
- [ ] Backup do banco recente e restauração já testada

**No corte**
- [ ] Mudar dono de scheduler, filas, webhook e canais conforme planejado
- [ ] Ativar o roteamento do módulo para o plus
- [ ] Fazer o fluxo principal manualmente com um tenant de teste

**Depois**
- [ ] Observar Pulse, logs, filas com falha e relatos de usuários durante o período combinado
- [ ] Conferir que não há execução duplicada de comando, job ou webhook
- [ ] Marcar o módulo como "legado desligável" em `_indice.md` (sem apagar código do legado ainda)
