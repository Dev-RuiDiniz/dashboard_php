# Sprint 15 — Plano Operacional de Execução

## 1) Escopo da sprint

### Entra na Sprint 15
- Evoluir exportações para maior fidelidade técnica no bootstrap:
  - XLSX em XML Spreadsheet explícito.
  - PDF com assinatura `%PDF-1.4` e estrutura mínima válida.
- Criar artefatos de golden files para validação de exportações.
- Adicionar testes automatizados de fidelidade dos exports.

### Não entra na Sprint 15
- Alteração de telas/UX.
- Mudança de endpoint/contrato HTTP.
- Introdução de engine externa de PDF/XLSX.

## 2) Referências obrigatórias
- `docs/DB_RULES_MYSQL.md`.
- `docs/SCREEN_RULES.md`.
- `docs/sprints/SPRINTS_CONSOLIDATED_AUDIT_AND_NEXT_PLAN.md` (Sprint 15).

## 3) Checklist
- [x] Evoluir `ExportService` para formatos mais fiéis.
- [x] Criar golden files em `docs/sprints/artifacts/golden_exports/`.
- [x] Adicionar `ReportsExportFidelityTest`.
- [x] Atualizar `ReportsExportTest` para novas garantias mínimas.
- [x] Atualizar `scripts/ci_checks.sh`.
- [x] Produzir `docs/sprints/SPRINT_15_REPORT.md`.

## 4) Critérios de aceite
- CSV segue estável e validado por golden file.
- XLSX passa a ser XML Spreadsheet válido de forma determinística.
- PDF passa a possuir assinatura `%PDF-1.4` e conteúdo esperado.
- Suíte local de checks permanece verde.

## 5) Plano de testes
- `bash scripts/ci_checks.sh`
- `php tests/Feature/ReportsExportFidelityTest.php`

## 6) Plano de rollback
- Reverter `ExportService` e testes de fidelidade para versão anterior em caso de incompatibilidade.
- Não há impacto de schema nem de contrato de rota nesta sprint.
