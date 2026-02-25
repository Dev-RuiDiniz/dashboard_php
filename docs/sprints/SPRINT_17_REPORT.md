# Sprint 17 — Relatório de Execução

## 1) O que foi feito
- Criado plano da sprint em `docs/sprints/SPRINT_17_EXECUTION.md`.
- Criado `scripts/reconciliation_report.php` para gerar relatório JSON de reconciliação por domínio (social, street, delivery, equipment, settings).
- Adicionado teste `tests/Feature/ReconciliationReportTest.php` cobrindo execução com massa local simulada.
- Atualizado `scripts/ci_checks.sh` para lint e execução do novo teste.
- Atualizado `README.md` e consolidado para refletir Sprint 17.

## 2) O que NÃO foi feito (e por quê)
- Não foi executada homologação real em staging por ausência de ambiente externo nesta execução local.
- Não foram executadas validações de volume/performance em base real (dependência externa).

## 3) Evidências
- `bash scripts/ci_checks.sh` → OK.
- `php tests/Feature/ReconciliationReportTest.php` → OK.

## 4) Riscos e pendências
- A reconciliação automatizada atual é mínima (contagens + amostras) e deve ser expandida com regras de consistência cruzada por operação.
- Próximas sprints devem cobrir hardening corporativo e janela piloto de cutover.

## 5) Checklist de conformidade
- [x] Respeitei `docs/DB_RULES_MYSQL.md` (sim — sem alteração de schema).
- [x] Respeitei `docs/SCREEN_RULES.md` (sim — sem alterações de telas).
- [x] Respeitei a Sprint 17 do plano adicional (sim — homologação integrada + reconciliação base).
- [x] Não criei campos/tabelas/telas inventadas (sim).
- [x] Rodei testes/lint/build (sim). Comandos: `bash scripts/ci_checks.sh`; `php tests/Feature/ReconciliationReportTest.php`.
