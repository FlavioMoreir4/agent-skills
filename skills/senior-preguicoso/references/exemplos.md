# Exemplos antes e depois

Os exemplos são ilustrativos e usam nomes fictícios. O ponto é a **proporção** entre o problema e a solução.

## 1. "Atualizar o telefone do responsável"

**Over-engineered** (9 arquivos para trocar um campo):

```
Contracts/ResponsavelRepositoryInterface.php
Repositories/EloquentResponsavelRepository.php
DTOs/AtualizarTelefoneResponsavelDTO.php
UseCases/AtualizarTelefoneResponsavelUseCase.php
Services/ResponsavelService.php
Http/Controllers/ResponsavelController.php
Http/Requests/AtualizarTelefoneRequest.php
Events/TelefoneResponsavelAtualizado.php   // nenhum listener
Providers/ResponsavelServiceProvider.php   // bind da interface
```

**Simples** (2 arquivos de produção):

```php
// Http/Requests/AtualizarTelefoneRequest.php
public function authorize(): bool
{
    return $this->user()->can('update', $this->route('responsavel'));
}

public function rules(): array
{
    return ['telefone' => ['required', 'string', 'max:20']];
}
```

```php
// Http/Controllers/ResponsavelController.php
public function atualizarTelefone(AtualizarTelefoneRequest $request, Responsavel $responsavel)
{
    $responsavel->update($request->validated());

    return back();
}
```

Sem Action (é CRUD), sem repository (Eloquent já é a abstração), sem DTO (o `validated()` basta), sem evento (ninguém escuta).

## 2. Duas ocorrências parecidas

Dois formulários montam a mesma lista de opções de unidade. **Duplique.** Só na terceira ocorrência, com os três usos reais na frente, extraia um escopo no model ou um composable. Extrair na segunda costuma gerar uma abstração que serve mal aos dois casos.

## 3. Quando a Action se justifica

Registrar o pagamento de uma parcela tem regra de negócio, transação e é chamado por tela e por webhook. Aqui uma Action faz sentido, e o domínio é rico (Financeiro):

```php
final class RegistrarPagamentoParcela
{
    public function handle(Parcela $parcela, Pagamento $pagamento): void
    {
        DB::transaction(function () use ($parcela, $pagamento) {
            $parcela = Parcela::lockForUpdate()->findOrFail($parcela->getKey());

            if ($parcela->estaPaga()) {
                return; // idempotente: webhook repetido não paga duas vezes
            }

            $parcela->registrarPagamento($pagamento); // transição de estado validada no model
        });
    }
}
```

Note o que **não** existe: interface, repository, factory. O que existe: transação, lock, idempotência e uma transição de estado explícita, que são as coisas que protegem dinheiro.

## 4. Frontend: tela com formulário

```vue
<script setup lang="ts">
import { useForm } from '@inertiajs/vue3'

const props = defineProps<{ responsavel: { id: number; nome: string; telefone: string } }>()

const form = useForm({ telefone: props.responsavel.telefone })
</script>
```

Estado local, `useForm`, componentes do shadcn-vue direto no template. Sem store, sem wrapper de input, sem composable de "formulário genérico". Se três telas repetirem exatamente o mesmo padrão, aí sim extraia um composable.

## 5. Tentação: "já que estou aqui"

Ao adicionar um campo na tela de matrícula, você nota que o service vizinho está confuso. **Não refatore.** Adicione o campo, e registre:

`- [ ] app/Services/MatriculaService.php — método calcularDesconto tem 4 responsabilidades — custo: médio — 2026-10-30`

Se o service impede o campo de funcionar corretamente, aí ele entra no escopo e você corrige o mínimo necessário.

## 6. Tentação: "e se um dia trocarmos o gateway?"

Existe um gateway (Asaas) e nenhum requisito de trocar. Não crie `PaymentGatewayInterface` com `AsaasGateway`, `StripeGateway` e uma factory. Use o cliente do Asaas diretamente, atrás de uma classe com métodos do **seu** negócio (se já houver uma para isolar a API externa). Se um dia houver um segundo gateway real, extraia a interface com os dois casos concretos na mão.
