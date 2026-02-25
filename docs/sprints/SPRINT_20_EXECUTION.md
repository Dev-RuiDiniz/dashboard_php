# Sprint 20 — Plano Operacional de Execução

## 1) Escopo da sprint

### Entra na Sprint 20
- Consolidar encerramento formal da trilha de migração no repositório.
- Criar artefato automatizado de prontidão para handover.
- Atualizar documentação final (README + consolidados + relatório final da sprint).

### Não entra na Sprint 20
- Execução de cutover real em ambiente produtivo.
- Mudanças de regras de negócio, telas ou schema.

## 2) Referências obrigatórias
- `docs/DB_RULES_MYSQL.md`
- `docs/SCREEN_RULES.md`
- `docs/sprints/SPRINT_16_RUNBOOK.md`
- `docs/sprints/SPRINT_19_REPORT.md`

## 3) Checklist
- [x] Criar script de handover (`scripts/handover_closure_report.php`).
- [x] Criar teste (`tests/Feature/HandoverClosureReportTest.php`).
- [x] Atualizar `scripts/ci_checks.sh`.
- [x] Criar `docs/sprints/SPRINT_20_REPORT.md`.
- [x] Atualizar consolidados e README com encerramento 01–20.

## 4) Critérios de aceite
- Script de handover retorna JSON válido com `handover_ready` e lista de artefatos.
- Teste da sprint passa no pipeline.
- Documentação consolidada reflete conclusão da trilha planejada.

## 5) Plano de testes
- `bash scripts/ci_checks.sh`
- `php tests/Feature/HandoverClosureReportTest.php`
- `php scripts/handover_closure_report.php | python -m json.tool`

## 6) Plano de rollback
- Reverter script/teste/documentação da Sprint 20 se necessário.
- Sem impacto em runtime, schema ou telas.
