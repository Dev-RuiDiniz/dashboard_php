# Sprint 13 — Plano Operacional de Execução

## 1) Escopo da sprint

### Entra na Sprint 13
- Expandir persistência relacional para domínios restantes do backend:
  - `DeliveryStore`
  - `EquipmentStore`
  - `SettingsStore`
- Criar migration SQL idempotente para tabelas de entregas, equipamentos/empréstimos e configuração de elegibilidade.
- Ampliar script de data migration JSON→MySQL para incluir os domínios acima.
- Adicionar teste automatizado de prontidão relacional para os domínios restantes.

### Não entra na Sprint 13
- Alteração de telas/UX.
- Mudança de contrato HTTP.
- Cutover produtivo de dados.

## 2) Referências obrigatórias
- `docs/DB_RULES_MYSQL.md`.
- `docs/SCREEN_RULES.md`.
- `docs/sprints/SPRINTS_CONSOLIDATED_AUDIT_AND_NEXT_PLAN.md` (Sprint 13 proposta).

## 3) Checklist
- [x] Criar migration SQL idempotente para entregas/equipamentos/settings.
- [x] Evoluir stores restantes para suporte opcional MySQL.
- [x] Expandir script de data migration JSON→MySQL para todos os domínios já migrados.
- [x] Adicionar teste de prontidão relacional dos domínios restantes.
- [x] Atualizar `scripts/ci_checks.sh`.
- [x] Criar `docs/sprints/SPRINT_13_REPORT.md`.

## 4) Critérios de aceite
- Fluxos atuais seguem funcionando no modo JSON (fallback).
- Migrations idempotentes criam tabelas e constraints básicas necessárias.
- Script de data migration suporta reexecução (upsert).
- Pipeline local de checks permanece verde.

## 5) Plano de testes
- `bash scripts/ci_checks.sh`
- `php tests/Feature/RemainingDomainsRelationalReadinessTest.php`
- `php -l scripts/migrate_json_to_mysql.php`

## 6) Plano de rollback
- Forçar `*_STORE_DRIVER=json` nos domínios migrados.
- Interromper execução de data migration até validar ambiente MySQL alvo.
- Reverter commit da sprint em caso de regressão.
