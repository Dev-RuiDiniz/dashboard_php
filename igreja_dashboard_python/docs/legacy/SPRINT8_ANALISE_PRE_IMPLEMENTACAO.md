# Sprint 8 — Análise Pré-Implementação (Relatório Mensal Consolidado Oficial)

## 1) Auditoria do que já existe

### monthly_closures
- Modelo `MonthlyClosure` já implementado com:
  - `month`, `year`, `status` (`OPEN`/`CLOSED`)
  - `summary_snapshot_json` (snapshot de fechamento)
  - `pdf_report_path` (PDF do fechamento)
  - `closed_by_user_id`, `closed_at`.
- Constraints atuais:
  - `month BETWEEN 1 AND 12`
  - unique `(month, year)`.

### Motor PDF institucional
- Motor único está em `src/app/pdf/report_engine.py` com:
  - Cabeçalho institucional (nome da instituição/sistema)
  - Seções textuais e tabulares
  - Rodapé padronizado
  - Geração de PDF em bytes (`generate_report_pdf`).

### Snapshot mensal base
- `src/app/closures/monthly_snapshot.py::build_monthly_snapshot()` já consolida:
  - `totals` (famílias, entregas, crianças, encaminhamentos, visitas, empréstimos etc.)
  - `breakdowns` (bairro, encaminhamentos, equipamentos)
  - `metadata` (mês/ano/fontes/usuário).

### Endpoints e UI de fechamento
- Rotas em `src/app/closures/routes.py`:
  - `GET /admin/fechamento`
  - `POST /admin/fechamento/close`
  - `GET /admin/fechamento/{year}/{month}/pdf`
  - `GET /admin/fechamento/{year}/{month}/snapshot.json`.
- Tela atual em `templates/admin_monthly_closure.html` já exibe status do fechamento e links para PDF/snapshot.

### Auditoria administrativa
- Existe `audit_logs` e helper `log_action()` em `src/app/services/audit.py`.
- Fechamento mensal já grava ação `MONTH_CLOSE`.

---

## 2) Mapeamento de fontes e definições de KPI

### Famílias atendidas
**Definição adotada:** famílias com retirada confirmada no mês (eventos de entrega), com fallback para legado de cestas (`food_baskets`) quando não houver retiradas.

- Fonte primária: `delivery_withdrawals` + `delivery_events.event_date`.
- Fonte fallback: `food_baskets` com status `DELIVERED` no mês/ano.

### Pessoas acompanhadas
**Definição adotada:** total de atendimentos sociais de pessoas em situação de rua no mês.

- Fonte: `street_services.service_date`.
- Observação: representa volume de acompanhamentos (serviços), não contagem distinta de pessoas.

### Total cestas
**Definição adotada:** total de entregas confirmadas no mês (`deliveries_count`) com prioridade para retiradas de evento; usa legado somente na ausência de retiradas no período.

### Visitas
**Definição adotada:** visitas executadas no mês.

- Fonte: `visit_executions.executed_at` (quando existir execução).
- Nota: snapshot atual usa `visit_requests.scheduled_date`; no oficial será priorizada execução para refletir ação realizada.

### Empréstimos
**Definição adotada:** empréstimos criados no mês.

- Fonte: `loans.loan_date`.
- Devoluções permanecem indicador separado (`loans.returned_at`).

---

## 3) Lock mensal e requisito de imutabilidade

- Regras de lock já existem em `src/app/closures/lock_guard.py` e bloqueiam alterações retroativas quando o mês está `CLOSED`.
- Para Sprint 8, o relatório oficial:
  - só poderá ser gerado após fechamento (`CLOSED`),
  - ficará imutável após geração,
  - exceção apenas com override administrativo explícito em variável de ambiente e auditoria específica.

---

## 4) Estratégia de comparativo mês anterior

- Buscar fechamento do mês imediatamente anterior.
- Prioridade de base anterior:
  1. `official_snapshot_json` (se já houver relatório oficial anterior)
  2. `summary_snapshot_json` (snapshot de fechamento).
- Se não houver base anterior fechada, relatório exibirá "sem base comparativa" e deltas como `N/A`.
- KPIs com variação absoluta e percentual:
  - `families_attended`
  - `people_followed`
  - `children_count`
  - `deliveries_count`
  - `referrals_count`
  - `visits_count`
  - `loans_count`
  - `pending_docs_count`
  - `pending_visits_count`
  - `avg_vulnerability`.

---

## 5) Estratégia de integridade (hash + imutabilidade)

1. Gerar bytes do PDF oficial.
2. Calcular SHA256 hexadecimal (`64` chars).
3. Persistir em `monthly_closures`:
   - `official_pdf_path`
   - `official_pdf_sha256`
   - `official_snapshot_json`
   - `official_signed_by_user_id`
   - `official_signed_at`.
4. Escrita de arquivo atômica (temp + rename), sem sobrescrita por padrão.
5. Bloquear nova geração se oficial já existir; permitir apenas com `ADMIN_OVERRIDE=true`, registrando ação de auditoria dedicada.

