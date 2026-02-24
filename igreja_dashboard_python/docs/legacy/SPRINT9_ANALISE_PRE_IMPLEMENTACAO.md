# Sprint 9 — Análise Pré-Implementação (Histórico Permanente + Comparativo)

## Auditoria obrigatória (Sprints 6–8)

### 1) Estado atual de `monthly_closures`
A modelagem já contém os campos necessários para histórico e relatório oficial:
- `status` com valores `OPEN` / `CLOSED`.
- `summary_snapshot_json` (fechamento mensal).
- `official_snapshot_json` (snapshot oficial).
- `official_pdf_path` e `official_pdf_sha256`.
- `official_signed_by_user_id` e `official_signed_at`.

Também já existem validações de integridade para hash SHA256 e vínculo com arquivo oficial.

### 2) Rotas de PDF oficial e snapshots
As rotas existentes em `/admin/fechamento` já cobrem:
- geração de relatório oficial;
- download do PDF oficial (`/admin/fechamento/{year}/{month}/relatorio-oficial.pdf`), com header `X-Content-SHA256`;
- leitura do snapshot de fechamento e snapshot oficial (admin-only).

### 3) Lock mensal (Sprint 7)
A proteção anti-retroativo está ativa via `require_month_open` e já é aplicada nas rotas de escrita (cestas, entregas, visitas, empréstimos, rua etc.).

### 4) Front-end atual
O frontend é SSR com Jinja2 + Bootstrap (CDN), com templates em `templates/` e navegação comum em `templates/base.html`.

### 5) Biblioteca de gráficos
Não há biblioteca de gráficos previamente integrada. Estratégia escolhida:
- **Chart.js via CDN** (simples para SSR, interativo, sem dependências de build).

## Endpoints planejados

### SSR
1. `GET /historico`
- Tabela mensal ordenada por ano/mês desc.
- Filtros por ano e status (`OPEN`/`CLOSED`/`OFICIAL`).
- Dados preferindo `official_snapshot_json`; fallback para `summary_snapshot_json`; fallback final zeros.

2. `GET /historico/{year}/{month}`
- KPI cards do mês (fonte oficial > summary > vazio).
- Metadados do oficial (assinatura, data, SHA256) quando disponível.
- Link para PDF oficial.
- Gráficos comparativos consumindo API de séries.
- Snapshot JSON técnico (admin-only).

### API JSON
3. `GET /api/historico/series?from=YYYY-MM&to=YYYY-MM`
- Retorna labels ordenadas e séries de métricas para gráficos.
- Fonte por mês: `official_snapshot_json` com fallback para `summary_snapshot_json`.

## Fontes de dados

- Tabela principal: `monthly_closures`.
- Snapshot priorizado por mês:
  1. `official_snapshot_json`
  2. `summary_snapshot_json`
  3. estrutura default com zeros

Métricas-alvo:
- `totals.families_attended`
- `totals.deliveries_count`
- `totals.children_count`
- `totals.referrals_count` (incluindo compatibilidade com formato legado em objeto)
- `indicators.avg_vulnerability` (fallback em `totals.avg_vulnerability`)

## Política de imutabilidade e validações

1. **Sem recálculo retroativo para meses fechados**:
- Histórico sempre lê snapshots persistidos.

2. **Lock mensal de escrita preservado**:
- Rotas mutáveis continuam bloqueando mudanças em meses `CLOSED`.

3. **Integridade visual/documental**:
- PDF oficial mantém header `X-Content-SHA256` ao download.
- Exibir hash na UI detalhada do mês.

4. **RBAC**:
- Leitura/Operador/Admin: acesso de consulta ao histórico e PDF oficial.
- Admin: acesso a snapshots JSON técnicos.
