# SPRINT 1 — Análise Pré-Implementação (Entregas por Evento)

## Auditoria obrigatória (estado encontrado)

## 1) Itens localizados

- **Modelo `FoodBasket`**: definido em `src/app/models/family.py` com relacionamento em `Family.food_baskets` e status por enum `FoodBasketStatus`.
- **Constraint mensal**: `UniqueConstraint("family_id", "reference_year", "reference_month", name="uq_food_basket_family_month")` no modelo `FoodBasket`.
- **Rotas existentes de cestas**: fluxo legado via SSR em `src/app/main.py`:
  - `POST /familias/{family_id}/cestas`
  - `POST /familias/{family_id}/cestas/{basket_id}/editar`
  - `POST /familias/{family_id}/cestas/{basket_id}/remover`
- **Relatórios CSV/XLSX**: rotas em `src/app/reports/routes.py` e geração reutilizável em `src/app/reports/exporters.py` (`build_csv`, `build_xlsx`).
- **Middleware de autenticação**: `@app.middleware("http")` em `src/app/main.py` (`auth_middleware`) com leitura de bearer/cookie JWT.
- **Sistema de RBAC**: em `src/app/core/auth.py` (`require_permissions`, `require_roles`, `ROLE_DEFINITIONS`) + modelo `User/Role` em `src/app/models/user.py`.
- **Logs estruturados**: formatter JSON em `src/app/core/logging.py` com logger `app.audit` usado nas rotas/middlewares.

## 2) Avaliação de reaproveitamento

### Reaproveitar
- Infra de autenticação/autorização atual (JWT + RBAC) para proteger novas rotas.
- Estrutura de exportação CSV/XLSX já consolidada.
- Heurística de vulnerabilidade do dashboard (`VULNERABILITY_ALERT_LEVELS`) e lógica de “sem cesta recente”.
- Modelo/consulta de famílias ativas (`Family.is_active`).

### Substituir / complementar
- Não há modelo orientado a evento para entregas (somente cesta mensal por família) → necessário novo domínio.
- Não há auditoria persistente em banco (`audit_logs`) → necessário criar tabela mínima.

## 3) Decisão arquitetural

### Decisão para `food_baskets`
**Opção C — Adaptado via camada de transição com legado em leitura e escrituras controladas por flag.**

- `food_baskets` permanece para histórico e compatibilidade com dashboard/relatórios já existentes.
- Novo fluxo operacional passa para `delivery_events`, `delivery_invites` e `delivery_withdrawals`.
- Escrita do legado pode ser descontinuada com `FEATURE_EVENT_DELIVERY=True` (sem remoção de tabela).

## Impacto em migrações

- Criar nova revisão Alembic reversível com:
  - `delivery_events`
  - `delivery_invites`
  - `delivery_withdrawals`
  - `audit_logs` (mínima, conforme escopo)
- Novos índices para consultas por evento, status, código e auditoria.
- Preservar integralmente `food_baskets` e sua unique mensal.

## Estratégia de compatibilidade

1. **Backward-compatible**: nenhuma rota existente será removida.
2. **Feature flag**: escrita no legado bloqueável por `FEATURE_EVENT_DELIVERY`.
3. **Histórico preservado**: relatórios anteriores continuam podendo usar `food_baskets`.
4. **Nova API dedicada**: `/entregas/eventos/*` para fluxo por evento.

