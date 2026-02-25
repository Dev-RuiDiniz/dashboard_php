# Sprint 10 — Runbook de Rollout/Rollback (Bootstrap)

## 1) Pré-checks
- Executar: `bash scripts/ci_checks.sh`
- Validar saúde: `GET /health` e `GET /ready`
- Validar autenticação e lockout básico.

## 2) Rollout (gradual)
1. Deploy em ambiente de stage.
2. Rodar smoke de endpoints críticos:
   - auth/login
   - reports/summary
   - eligibility/check
   - equipment/loans
3. Monitorar logs JSON (`status`, `duration_ms`, `request_id`).
4. Promover para produção apenas com smoke verde.

## 3) Rollback
1. Reverter para commit/tag anterior estável.
2. Reiniciar serviço.
3. Validar `GET /health` e `GET /ready`.
4. Reexecutar smoke mínimo de login e endpoint de domínio crítico.

## 4) Critérios Go/No-Go
- Go: checks, smoke e métricas mínimas sem degradação.
- No-Go: aumento anômalo de 5xx, falha de autenticação, latência fora do baseline.
