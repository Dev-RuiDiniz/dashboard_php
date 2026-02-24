# Regras de Lock Mensal

## Princípio
Quando um mês está em `CLOSED` na tabela `monthly_closures`, alterações retroativas de fatos daquele mês são bloqueadas com erro `409` e mensagem **"Mês fechado"**.

## Entidades cobertas e regra de pertencimento ao mês

- **DeliveryEvent / DeliveryInvite / DeliveryWithdrawal**: mês de `delivery_events.event_date`.
- **FoodBasket (legacy)**: `reference_month/reference_year`.
- **VisitRequest / VisitExecution**: mês de `visit_requests.scheduled_date`.
- **StreetService**: mês de `service_date`.
- **Referral**: mês de `referral_date`.
- **Loan (empréstimo/devolução)**:
  - Empréstimo: mês de `loan_date`.
  - Devolução: bloqueio baseado no mês do empréstimo originador (proteção retroativa).

## Pontos de interceptação

Centralizado em `src/app/closures/lock_guard.py`:
- `is_month_closed(db, month, year)`
- `require_month_open(db, target_date|month/year)`

Aplicado antes de persistir em rotas de escrita (`main.py` e `deliveries/routes.py`).

## Operações permitidas com mês fechado
- Leitura/listagens
- Download de PDF oficial
- Leitura do snapshot JSON
- Alterações em meses ainda abertos
