# Sprint 16 — Plano Operacional de Execução

## 1) Escopo da sprint

### Entra na Sprint 16
- Consolidar plano final de produção assistida (cutover) com critérios Go/No-Go.
- Definir checklist operacional de rollout, rollback e reconciliação de dados.
- Publicar runbook final de encerramento da migração.
- Encerrar trilha de sprints com auditoria consolidada 01–16.

### Não entra na Sprint 16
- Implementação de novas features de negócio.
- Criação/alteração de telas.
- Mudanças de schema adicionais.

## 2) Referências obrigatórias
- `docs/DB_RULES_MYSQL.md`.
- `docs/SCREEN_RULES.md`.
- `docs/sprints/SPRINTS_CONSOLIDATED_AUDIT_AND_NEXT_PLAN.md`.

## 3) Checklist
- [x] Criar runbook final de cutover/rollback (`SPRINT_16_RUNBOOK.md`).
- [x] Criar plano de execução da sprint (`SPRINT_16_EXECUTION.md`).
- [x] Criar relatório da sprint (`SPRINT_16_REPORT.md`).
- [x] Atualizar consolidado de auditoria para 01–16.
- [x] Atualizar README com estado final das sprints.
- [x] Rodar checks automatizados.

## 4) Critérios de aceite
- Runbook final documenta pré-checks, janela, execução, validação e rollback.
- Critérios Go/No-Go explícitos e rastreáveis.
- Evidências de validação local registradas no relatório.

## 5) Plano de testes
- `bash scripts/ci_checks.sh`
- `php tests/Feature/OpenApiContractTest.php`
- `php tests/Feature/ReportsExportFidelityTest.php`

## 6) Plano de rollback
- Reverter para o commit/tag estável pré-Sprint 16.
- Manter operação com runbook Sprint 10 enquanto ajusta documentação final.
- Sem impacto de runtime esperado (sprint documental/operacional).
