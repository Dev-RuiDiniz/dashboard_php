# Motor de elegibilidade

Módulo: `src/app/eligibility/engine.py`.

## Regras

Uma família é elegível somente quando **todas** condições abaixo são verdadeiras:

1. Vulnerabilidade >= `min_vulnerability_level`
2. Se `require_documentation_complete=true`, documentação deve estar completa
3. Meses sem entrega >= `min_months_since_last_delivery`
4. Se `delivery_month_limit > 0`, total de entregas no mês atual deve ser menor que o limite

## Fonte da "última entrega" (prioridade)

1. `delivery_withdrawals.confirmed_at` (retirada confirmada por evento)
2. Fallback para `food_baskets` com status `DELIVERED` (mês/ano convertido para data de referência)

Quando ambas existem, considera-se a data mais recente.

## Limite mensal

Contagem mensal soma:

- retiradas confirmadas (`delivery_withdrawals`) no mês corrente
- cestas legacy entregues (`food_baskets`) no mês corrente

## Motivos de inelegibilidade (debug/admin)

- `DOC_PENDING`
- `LOW_VULNERABILITY`
- `RECENT_DELIVERY`
- `MONTH_LIMIT_REACHED`
