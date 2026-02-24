# Transição: Food Baskets → Delivery Events

## Estratégia adotada

- `food_baskets` permanece como **histórico legado**.
- Novo módulo de entregas por evento usa:
  - `delivery_events`
  - `delivery_invites`
  - `delivery_withdrawals`
- Auditoria persistente mínima em `audit_logs`.

## Feature flag de transição

- Configuração: `FEATURE_EVENT_DELIVERY` (setting `feature_event_delivery`).
- Quando `True`, o endpoint legado de criação de cesta (`POST /familias/{family_id}/cestas`) é bloqueado para evitar novos registros fora do fluxo de evento.
- Leitura de histórico legado permanece disponível.

## Compatibilidade

- Sem remoção imediata de tabelas antigas.
- Sem quebra de rotas de visualização existentes.
- Permite migração gradual operacional e treinamento da equipe.

