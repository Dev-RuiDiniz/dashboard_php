# Sprint 19 — Plano Operacional de Execução

## 1) Escopo da sprint

### Entra na Sprint 19
- Implementar utilitário de decisão de janela piloto (GO/NO_GO) com base em artefatos de segurança e reconciliação.
- Adicionar teste automatizado para o dry-run de cutover.
- Atualizar documentação consolidada para refletir Sprint 19.

### Não entra na Sprint 19
- Execução de cutover real em produção.
- Mudanças de schema, rotas ou telas.

## 2) Referências obrigatórias
- `docs/DB_RULES_MYSQL.md`
- `docs/SCREEN_RULES.md`
- `docs/sprints/SPRINT_16_RUNBOOK.md`
- `docs/sprints/SPRINT_18_REPORT.md`

## 3) Checklist
- [x] Criar `scripts/pilot_cutover_dry_run.php`.
- [x] Criar `tests/Feature/PilotCutoverDryRunTest.php`.
- [x] Atualizar `scripts/ci_checks.sh`.
- [x] Criar `docs/sprints/SPRINT_19_REPORT.md`.

## 4) Critérios de aceite
- Script retorna JSON válido com `decision` e `failed_checks`.
- Cenário de referência do teste resulta em decisão `GO`.
- Pipeline local permanece verde.

## 5) Plano de testes
- `bash scripts/ci_checks.sh`
- `php tests/Feature/PilotCutoverDryRunTest.php`
- `php scripts/pilot_cutover_dry_run.php --input-dir /tmp`

## 6) Plano de rollback
- Reverter script/teste de dry-run caso necessário.
- Sem impacto em runtime das APIs ou schema.
