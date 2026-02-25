# Sprint 10 — Plano Operacional de Execução

## 1) Escopo da sprint

### Entra na Sprint 10
- Hardening técnico mínimo de segurança no bootstrap.
- Controle de tentativas de login (rate limit/lockout básico).
- Documento de rollout/rollback e runbook operacional.

### Não entra na Sprint 10
- Migração real de base de produção (cutover real depende ambiente).
- DAST/SAST corporativo completo.
- Mudanças de tela/UX.

## 2) Referências obrigatórias
- `AUDITORIA_E_PLANO_MIGRACAO_PYTHON_PHP_10_SPRINTS.md` (Sprint 10).
- `docs/DB_RULES_MYSQL.md`.
- `docs/SCREEN_RULES.md`.

## 3) Checklist
- [x] Implementar lockout/rate limit básico no login.
- [x] Aplicar headers de segurança HTTP no entrypoint.
- [x] Criar runbook de rollout/rollback em docs.
- [x] Adicionar testes automatizados da sprint.
- [x] Produzir `docs/sprints/SPRINT_10_REPORT.md`.
