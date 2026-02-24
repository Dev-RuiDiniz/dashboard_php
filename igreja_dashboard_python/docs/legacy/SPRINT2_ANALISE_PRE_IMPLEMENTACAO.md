# SPRINT 2 — Análise Pré-Implementação (Módulo de Crianças)

## 1) Auditoria obrigatória (estado encontrado)

### Modelagem atual de Famílias e Dependentes
- `Family` e `Dependent` estão em `src/app/models/family.py`.
- `Family` possui `is_active`, `created_at`, CPF único (`responsible_cpf`) e relacionamento `dependents` com `cascade="all, delete-orphan"`.
- `Dependent` possui FK obrigatória `family_id`, `name` e `birth_date` obrigatórios; CPF opcional com `unique=True`.
- Regras de validação em rotas SSR (`src/app/main.py`):
  - CPF normalizado/validado por `_validate_cpf` e conflito por `_cpf_conflict`.
  - Datas parseadas por `_parse_date`.
  - Bloqueio de criação/edição de dependente quando família está inativa.

### Padrão de rotas SSR
- Rotas principais SSR vivem em `src/app/main.py` com `templates = Jinja2Templates(directory="templates")`.
- Fluxo de páginas segue padrão list → form (novo/editar) → detalhe:
  - Famílias: `/familias`, `/familias/nova`, `/familias/{id}/editar`, `/familias/{id}`.
  - Dependentes: formularios aninhados na família com template dedicado `templates/dependent_form.html`.
- Estrutura de contexto comum via `_template_context(request)` e uso de `TemplateResponse`.

### Padrão RBAC
- Implementado em `src/app/core/auth.py` via `require_permissions` e `require_roles`.
- Perfis atuais em `ROLE_DEFINITIONS`: `Admin`, `Operador`, `Leitura`.
- Para SSR de famílias usa-se:
  - leitura: `require_permissions("view_families")`
  - escrita: `require_permissions("manage_families")`

### Padrão de export XLSX/CSV
- Utilitários em `src/app/reports/exporters.py`: `build_csv(headers, rows)` e `build_xlsx(sheet_name, headers, rows)`.
- Reuso em `src/app/reports/routes.py` e `src/app/deliveries/routes.py`.

### Eventos (Sprint 1)
- Entidades em `src/app/models/delivery.py`:
  - `DeliveryEvent` (status `OPEN/CLOSED`)
  - `DeliveryInvite` (status `INVITED/WITHDRAWN/NO_SHOW`)
  - `DeliveryWithdrawal`
- Retirada confirmada atualiza convite para `WITHDRAWN` em `/entregas/eventos/{event_id}/retirada/{family_id}`.
- Export de evento existente em CSV/XLSX (`/entregas/eventos/{id}/export.csv|xlsx`).

### PDF no repositório
- Não há geração PDF atualmente (sem rotas utilitárias de PDF e sem dependência dedicada).
- Decisão para Sprint 2: adicionar módulo isolado `src/app/pdf/` com ReportLab (offline, simples, sem dependência de engine externa).

## 2) Decisão de design (A/B)

### Escolha: **A) Entidade separada `children` vinculada à `family`**

Motivos:
1. O escopo exige explicitamente tabela `children`.
2. Mantém compatibilidade total com `dependents` sem quebrar fluxo existente.
3. Permite regras e relatórios próprios de crianças (filtros de idade/sexo e lista por evento).

Compatibilidade:
- `dependents` permanece inalterado para não quebrar telas/rotas existentes.
- `children` entra como domínio novo paralelo, com relação direta a `families`.

## 3) Reaproveitamento planejado
- Reutilizar `require_permissions` para RBAC (Leitura=ver, Operador/Admin=gerenciar).
- Reutilizar helpers de parse/validação já existentes em `main.py` (`_parse_date`, `_require_value`).
- Reutilizar exportadores `build_xlsx` e padrão de resposta `Response`.
- Reutilizar padrão de templates Bootstrap/Jinja adotado no módulo de famílias.

## 4) Impacto esperado

### Banco de dados
- Nova migration Alembic para:
  - criar `children`
  - adicionar `has_children_list` em `delivery_events`
  - índices por `family_id` e `birth_date`

### Backend
- Novo model SQLAlchemy `Child` e relação `Family.children`.
- Novas rotas SSR:
  - CRUD completo em `/criancas*`
  - listagem por evento em `/entregas/eventos/{id}/criancas`
  - exports `/export.xlsx` e `/export.pdf`

### Front-end SSR
- Novos templates:
  - `children_list.html`
  - `children_form.html`
  - `children_detail.html`
  - `event_children_list.html`

### Testes
- Novos testes para CRUD de crianças, regra de confirmação por evento e export.
- Cobertura opcional de PDF conforme disponibilidade da implementação.
