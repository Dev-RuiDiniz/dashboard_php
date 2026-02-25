# Sprint 07 — Plano Operacional de Execução

## 1) Escopo da sprint

### Entra na Sprint 07
- Exportações de relatórios em CSV, XLSX e PDF (bootstrap técnico).
- Endpoints de exportação em `/reports/export.csv`, `/reports/export.xlsx`, `/reports/export.pdf`.
- Evidências básicas de geração de conteúdo com dados de famílias.

### Não entra na Sprint 07
- Fidelidade visual final de layout institucional de PDF (será refinada).
- Exportações avançadas por todos os domínios.
- Telas/UX.
- Migrações/schema.

## 2) Referências obrigatórias
- `AUDITORIA_E_PLANO_MIGRACAO_PYTHON_PHP_10_SPRINTS.md` (Sprint 07).
- `docs/DB_RULES_MYSQL.md`.
- `docs/SCREEN_RULES.md`.

## 3) Objetivo e backlog
- Objetivo: entregar paridade inicial de exportadores.
- Backlog:
  - CSV de famílias;
  - XLSX básico (conteúdo tabular);
  - PDF básico (conteúdo textual).

## 4) Checklist
- [x] Implementar exportador CSV.
- [x] Implementar exportador XLSX básico.
- [x] Implementar exportador PDF básico.
- [x] Expor endpoints de exportação.
- [x] Adicionar testes automatizados de export.
- [x] Produzir `docs/sprints/SPRINT_07_REPORT.md`.
