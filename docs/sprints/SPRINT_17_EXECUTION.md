# Sprint 17 — Plano Operacional de Execução

## 1) Escopo da sprint

### Entra na Sprint 17
- Consolidar etapa de homologação integrada em staging (pré-cutover real).
- Criar utilitário de reconciliação por domínio para suporte operacional da virada.
- Documentar checklist de homologação e critérios de aceite da etapa.

### Não entra na Sprint 17
- Mudança de regras de negócio.
- Mudança de schema.
- Criação/alteração de telas.

## 2) Referências obrigatórias
- `docs/DB_RULES_MYSQL.md`
- `docs/SCREEN_RULES.md`
- `docs/sprints/SPRINT_16_RUNBOOK.md`
- `docs/sprints/SPRINTS_MASTER_CONSOLIDATION_REPORT.md`

## 3) Checklist
- [x] Criar script de reconciliação (`scripts/reconciliation_report.php`).
- [x] Criar teste automatizado para reconciliação (`ReconciliationReportTest`).
- [x] Atualizar `scripts/ci_checks.sh`.
- [x] Produzir `docs/sprints/SPRINT_17_REPORT.md`.

## 4) Critérios de aceite
- Script gera JSON válido com contagens e amostras por domínio.
- Teste automatizado da reconciliação executa com sucesso.
- Pipeline local permanece verde.

## 5) Plano de testes
- `bash scripts/ci_checks.sh`
- `php tests/Feature/ReconciliationReportTest.php`
- `php scripts/reconciliation_report.php --data-dir /tmp` (smoke)

## 6) Plano de rollback
- Reverter script/teste de reconciliação caso necessário.
- Sem impacto em rotas, schema ou telas.
