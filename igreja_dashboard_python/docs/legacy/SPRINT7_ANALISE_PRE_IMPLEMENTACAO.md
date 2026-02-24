# Sprint 7 — Análise pré-implementação

## 1) Mapeamento do estado atual

### Relatórios mensais atuais
- O módulo `reports/queries.py` já usa `year/month` em relatórios de cestas (`FoodBasket.reference_year/reference_month`) e visitas (`VisitRequest.scheduled_date` com `extract`).【F:src/app/reports/queries.py†L30-L41】【F:src/app/reports/queries.py†L152-L163】
- O relatório de bairros também aplica filtro mensal/ano para cestas entregues (legado).【F:src/app/reports/queries.py†L166-L201】

### Entidades-fato por mês
- Entregas por evento: `delivery_events`, `delivery_invites`, `delivery_withdrawals` (fonte prioritária).【F:src/app/models/delivery.py†L32-L129】
- Entregas legadas: `food_baskets` por `reference_month/reference_year`.【F:src/app/models/family.py†L168-L198】
- Atendimentos rua/ficha social parcial: `street_services.service_date`, `referrals.referral_date`, `visit_requests.scheduled_date`.【F:src/app/models/street.py†L57-L99】【F:src/app/models/family.py†L213-L247】
- Crianças: `children` vinculadas a `family_id`.【F:src/app/models/family.py†L131-L166】
- Equipamentos: `loans.loan_date`, `loans.returned_at`, `status`.【F:src/app/models/equipment.py†L55-L77】
- Pendências: dashboard/report já inferem pendência documental e visitas pendentes/atrasadas por regras em consultas e status. 【F:src/app/reports/queries.py†L66-L129】

### RBAC Admin atual
- Gate de permissões/roles em `require_roles` e `require_permissions`.【F:src/app/core/auth.py†L59-L74】
- Áreas administrativas existentes em `/admin/users`, `/admin/config`, `/admin/audit` no `main.py`.【F:src/app/main.py†L921-L1154】

### Audit log
- Tabela/modelo `AuditLog` já existente, com helper `log_action` para ações administrativas e operacionais.【F:src/app/models/delivery.py†L131-L149】【F:src/app/services/audit.py†L56-L71】

### PDF e armazenamento
- Engine padrão em `pdf/report_engine.py::generate_report_pdf`.【F:src/app/pdf/report_engine.py†L190-L240】
- Exportações atuais retornam bytes em response, sem persistência oficial de PDF mensal em storage dedicado.

## 2) Definições da Sprint 7

### Fonte de verdade para entregas
1. **Prioridade**: `delivery_withdrawals` associadas a `delivery_events.event_date` no mês/ano.
2. **Fallback legacy**: `food_baskets` com `status=DELIVERED` no `reference_month/reference_year` quando não houver withdrawals.

### Estratégia de persistência do PDF
- Escolha MVP: **A) disco local do servidor**.
- Diretório base configurável por `REPORTS_DIR` (default `data/reports`).
- Convenção: `data/reports/monthly/{year}-{month:02d}-fechamento.pdf`.
- Escrita atômica: arquivo temporário + rename.

### Rotas/bloqueios planejados
- Bloquear escrita em mês fechado para: entregas (eventos/convites/retiradas), cestas legacy, visitas sociais, atendimentos rua, encaminhamentos e operações de empréstimo/devolução que alteram fatos do mês.
- Permitir leitura total e download de snapshot/PDF oficial.

### Compatibilidade legacy
- Snapshot agrega `delivery_withdrawals` e, na ausência, usa `food_baskets_legacy`.
- Relatórios existentes não são removidos; fechamento adiciona camada de governança (snapshot imutável + lock).
