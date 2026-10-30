# Eloquent como camada anticorrupção

Enquanto o schema está congelado, os models do plus escondem o formato legado. O resto do código (controllers, Actions, Resources, props Inertia, Vue) só enxerga nomes e tipos limpos. Quando o schema for corrigido depois do corte, só o model muda.

**Os nomes de tabela e coluna abaixo são fictícios.** Use os reais do legado, conferidos na análise do módulo.

## Regras

1. Um model por tabela usada pelo módulo, com o nome do conceito no plus (não o nome da tabela).
2. Nomes legados ficam **dentro** do model e não vazam para controllers, Resources, props Inertia, testes ou Vue.
3. Valores mágicos (flags, códigos de uma letra, 0/1 ambíguos) viram **enums** via cast.
4. Relações usam chaves explícitas, mesmo quando o legado não tem FK no banco.
5. Consultas recorrentes viram `scope` no model, com nome do negócio.
6. Aplique o mesmo escopo de tenant que o legado aplica (global scope ou equivalente), e teste.
7. Comece em **modo leitura**. Habilite escrita só depois de mapear as invariantes do legado para aquela tabela.

## Exemplo (fictício)

```php
<?php

namespace App\Models;

use App\Enums\SituacaoResponsavel;
use Illuminate\Database\Eloquent\Casts\Attribute;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Responsavel extends Model
{
    protected $table = 'tb_resp';            // nome legado fica só aqui
    protected $primaryKey = 'cod_resp';
    public $timestamps = false;              // só se a tabela realmente não tem as colunas

    protected function casts(): array
    {
        return [
            'situacao' => SituacaoResponsavel::class,   // 'A' / 'I' / 'C' viram enum
            'dt_nasc'  => 'date',
        ];
    }

    // Atributos com nome limpo sobre colunas legadas
    protected function nome(): Attribute
    {
        return Attribute::make(
            get: fn (mixed $value, array $attributes) => $attributes['nm_resp'],
            set: fn (string $value) => ['nm_resp' => $value],
        );
    }

    protected function ativo(): Attribute
    {
        return Attribute::get(
            fn (mixed $value, array $attributes) => $attributes['situacao'] === SituacaoResponsavel::Ativo->value
        );
    }

    // Relações com chaves explícitas
    public function contratos(): HasMany
    {
        return $this->hasMany(Contrato::class, 'cod_resp', 'cod_resp');
    }

    public function unidade(): BelongsTo
    {
        return $this->belongsTo(Unidade::class, 'cod_unid', 'cod_unid');
    }

    // Consulta com nome de negócio
    public function scopeAtivos($query)
    {
        return $query->where('situacao', SituacaoResponsavel::Ativo->value);
    }
}
```

```php
enum SituacaoResponsavel: string
{
    case Ativo = 'A';
    case Inativo = 'I';
    case Cancelado = 'C';
}
```

Na saída para o frontend, use `JsonResource` (ou array explícito) com nomes limpos:

```php
return [
    'id'    => $this->getKey(),
    'nome'  => $this->nome,
    'ativo' => $this->ativo,
];
```

## O que não fazer

- Não crie uma camada paralela de "entidades de domínio" mapeadas por repository só para renomear colunas. O model já faz esse papel.
- Não replique o schema legado em DTOs. Se um DTO só espelha o model, não é necessário.
- Não use views ou colunas geradas no banco para "limpar" o schema agora. Isso é mudança de schema.
- Não escreva em coluna derivada do legado sem saber quem a recalcula.

## Quando o model começa a ficar mentiroso

Se um model precisa de muita lógica para esconder o schema (mais de uma tabela para um conceito, colunas que mudam de significado conforme o estado), é sinal de que aquele ponto merece correção de schema **depois do corte**. Registre em `docs/divida.md` com a tabela e o motivo, e trate com `expand-contract.md`.
