# Sprint 5 — Análise pré-implementação

## 1) Auditoria do estado atual

### 1.1 Onde e como o dashboard calcula alertas hoje

- O dashboard gerencial usa `src/app/dashboard/service.py` + `src/app/dashboard/queries.py` para KPIs e lista de alertas.
- Regras atuais identificadas:
  - **"Sem cesta há X meses"**: `count_families_without_recent_basket` usa `FoodBasket` entregue e compara índice mês/ano com `date.today()`; threshold default = `3`.
  - **Vulnerabilidade + baixa assistência**: `count_families_with_alerts` e `alert_distribution` usam `VULNERABILITY_ALERT_LEVELS = {HIGH, EXTREME}` e exigem `>= 2` meses sem cesta para alerta.
  - **Pendências/visitas**: `social_visits_overview` calcula visitas pendentes, atrasadas e concluídas no mês via `VisitRequest.status` e `scheduled_date`.
- Fora do dashboard, há regras repetidas em `src/app/main.py`:
  - `_build_basket_alerts`: alerta textual por tempo sem cesta e vulnerabilidade alta/extrema.
  - `_build_visit_alerts`: alerta de visitas pendentes/atrasadas por família.

### 1.2 Campos existentes em Family

`Family` já possui:
- `socioeconomic_profile` (Text)
- `documentation_status` (Text)
- `vulnerability` (enum `VulnerabilityLevel` com valores Sem vulnerabilidade/Baixa/Média/Alta/Extrema)
- **Não existe** `last_delivery`/`last_basket` persistido; hoje é derivado por query em `FoodBasket`.

### 1.3 Como "entrega" é medida hoje

- **Legacy**: `FoodBasket` com status `DELIVERED` é a base principal para dashboard, alertas e contagens mensais.
- **Sprint 1**: existe módulo de eventos com `DeliveryEvent`, `DeliveryInvite`, `DeliveryWithdrawal`.
  - Retirada/entrega confirmada é registrada em `DeliveryWithdrawal.confirmed_at`.
  - O convite automático atual (`_eligible_families_auto`) ainda usa apenas `FoodBasket` (não usa withdrawals).

### 1.4 Existe módulo de configurações admin hoje?

- Não há módulo de "configurações do sistema" persistidas em BD.
- Existem páginas admin SSR para:
  - `/admin/users`
  - `/admin/consentimento`
  - `/admin/audit`

### 1.5 Padrão de páginas admin SSR + RBAC

- Rotas SSR em `src/app/main.py` com `templates.TemplateResponse(...)`.
- RBAC por permissões em dependências FastAPI (`Depends(require_permissions(...))`) e flags de menu via `_template_context` (`can_manage_users`, etc.).
- Padrão de POST admin:
  - validações server-side,
  - commit,
  - redirect `303` para GET correspondente,
  - resposta 400 com template em caso de erro de validação.

## 2) Decisão técnica: modelagem de `system_settings`

### Opções
- **A)** key/value
- **B)** tabela single-row com colunas fixas

### Decisão
- **Escolha: B (single-row)** para esta sprint.

### Motivo
- Menor complexidade para MVP e leitura direta no engine.
- Reduz risco de inconsistência de tipos/chaves em parâmetros críticos de elegibilidade.
- Mantém possibilidade de evolução futura para key/value (migração incremental viável).

## 3) Fonte para "última entrega" e prioridade

Para o motor de elegibilidade:
1. **Prioridade 1:** `DeliveryWithdrawal.confirmed_at` (entrega confirmada por evento).
2. **Fallback:** `FoodBasket` entregue (`reference_year`/`reference_month` convertido para data representativa do mês).

Regra prática de comparação:
- usar a data mais recente entre as duas fontes quando ambas existirem,
- considerar mês atual para cálculo de meses sem entrega.

## 4) Estratégia de cache e atualização imediata

- **Sem cache de longa duração** para elegibilidade/config.
- `system_settings` será lido a cada request de dashboard/listagem elegível/admin update.
- Após `POST /admin/config`, persistência em BD e refletir imediatamente em consultas subsequentes (sem restart).

## 5) Endpoints/telas a criar

### SSR admin
- `GET /admin/config` — exibe formulário de parâmetros.
- `POST /admin/config` — valida e salva parâmetros.
- Template: `templates/admin_config.html`.

### Engine
- `src/app/eligibility/engine.py`
  - `get_system_settings(db)`
  - `compute_family_eligibility(db, family_id, settings)`
  - `list_eligible_families(db, settings, limit=...)`

### Dashboard
- Nova seção "Famílias elegíveis sugeridas" em `templates/dashboard/dashboard.html`.
- Integração via `src/app/dashboard/service.py` (consumindo engine).
- Suporte a filtros de bairro e limite (top N) pela rota `/dashboard`.

## 6) Integração opcional Sprint 1

- Reaproveitar engine no fluxo de convite automático (`/entregas/eventos/{id}/convidar`, modo automático), evitando regra duplicada.
