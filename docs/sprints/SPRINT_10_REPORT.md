# Sprint 10 — Relatório de Execução

## 1) O que foi feito
- Criado plano operacional da sprint em `docs/sprints/SPRINT_10_EXECUTION.md`.
- Implementado lockout/rate limit básico de login com `AuthThrottleStore` em `src/Domain/AuthThrottleStore.php`.
- Evoluído `src/Http/Kernel.php` para bloquear autenticação após tentativas inválidas (`429`).
- Aplicados headers de segurança HTTP no entrypoint `public/index.php`.
- Criado runbook de rollout/rollback em `docs/sprints/SPRINT_10_RUNBOOK.md`.
- Adicionado teste de hardening em `tests/Feature/SecurityHardeningTest.php`.
- Atualizados `scripts/ci_checks.sh` e `README.md`.

## 2) O que NÃO foi feito (e por quê)
- Não foi realizado cutover real de produção (depende ambiente operacional externo).
- Não foram executadas ferramentas corporativas SAST/DAST completas (fora do escopo local desta execução).
- Não houve alteração de telas ou schema.

## 3) Evidências
- `bash scripts/ci_checks.sh` → OK.
- Smoke HTTP manual:
  - headers de segurança presentes em `/health`;
  - sequência de login inválido retorna lockout (`401 ... 429`).

## 4) Riscos e pendências
- Lockout atual é simplificado (arquivo local JSON); em produção deve evoluir para backend distribuído.
- Necessidade de hardening avançado (SAST/DAST, carga, DR drill) no pipeline de produção.

## 5) Encerramento do plano
- Sprint 10 concluída no escopo técnico bootstrap.
- Próximo marco: consolidação de produção (infra, dados e observabilidade operacional).

## 6) Checklist de conformidade
- [x] Respeitei `docs/DB_RULES_MYSQL.md` (sim — sem mudanças de schema).
- [x] Respeitei `docs/SCREEN_RULES.md` (sim — sem criação/alteração de telas).
- [x] Respeitei a Sprint 10 do plano (sim — hardening + runbook rollout/rollback).
- [x] Não criei campos/tabelas/telas inventadas fora do escopo (sim).
- [x] Rodei testes/lint/build (sim). Comandos: `bash scripts/ci_checks.sh`; `php -S 127.0.0.1:8180 -t public` + `curl` para headers e lockout.
