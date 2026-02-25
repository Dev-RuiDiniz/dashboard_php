# Sprint 18 — Plano Operacional de Execução

## 1) Escopo da sprint

### Entra na Sprint 18
- Implementar baseline automatizado de postura de segurança operacional.
- Adicionar verificação de presença de artefatos críticos e variáveis essenciais.
- Incluir teste automatizado para relatório de postura.

### Não entra na Sprint 18
- Alterações de telas/UX.
- Mudanças de schema.
- Introdução de ferramentas externas SAST/DAST (somente preparação e baseline documental/automatizado local).

## 2) Referências obrigatórias
- `docs/DB_RULES_MYSQL.md`
- `docs/SCREEN_RULES.md`
- `docs/sprints/SPRINT_16_RUNBOOK.md`
- `docs/sprints/SPRINTS_MASTER_CONSOLIDATION_REPORT.md`

## 3) Checklist
- [x] Criar script `scripts/security_posture_report.php`.
- [x] Criar teste `tests/Feature/SecurityPostureReportTest.php`.
- [x] Atualizar `scripts/ci_checks.sh`.
- [x] Atualizar documentação e relatório da sprint.

## 4) Critérios de aceite
- Script de postura retorna JSON válido com `checks` e `summary`.
- Teste automatizado da postura passa em ambiente local.
- Pipeline local permanece verde.

## 5) Plano de testes
- `bash scripts/ci_checks.sh`
- `php tests/Feature/SecurityPostureReportTest.php`
- `php scripts/security_posture_report.php`

## 6) Plano de rollback
- Reverter script e teste caso incompatibilidade operacional.
- Sem impacto em schema, rotas ou telas.
