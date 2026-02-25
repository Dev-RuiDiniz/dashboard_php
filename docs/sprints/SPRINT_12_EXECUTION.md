# Sprint 12 — Plano Operacional de Execução

## 1) Escopo da sprint

### Entra na Sprint 12
- Expandir persistência relacional para o módulo Street (`people/referrals`) mantendo fallback JSON.
- Criar migration SQL idempotente para tabelas `street_residents` e `street_referrals`.
- Criar script idempotente de migração de dados JSON→MySQL (`social` + `street`).
- Adicionar teste automatizado de prontidão relacional do módulo Street.

### Não entra na Sprint 12
- Migração relacional completa de `deliveries`, `equipment` e `settings`.
- Alteração de telas/UX.
- Cutover de dados em ambiente de produção.

## 2) Referências obrigatórias
- `docs/DB_RULES_MYSQL.md`.
- `docs/SCREEN_RULES.md`.
- `docs/sprints/SPRINTS_CONSOLIDATED_AUDIT_AND_NEXT_PLAN.md` (Sprint 12 proposta).

## 3) Checklist
- [x] Criar migration SQL `street_residents` + `street_referrals` com FK e índices.
- [x] Evoluir `StreetStore` para modo opcional MySQL.
- [x] Criar script de data migration JSON→MySQL com operação idempotente.
- [x] Adicionar teste de prontidão relacional de street.
- [x] Atualizar pipeline local de checks.
- [x] Produzir `docs/sprints/SPRINT_12_REPORT.md`.

## 4) Critérios de aceite
- Fluxos atuais do módulo Street continuam operando no modo JSON sem regressão.
- Migration SQL aplica criação idempotente de tabelas com constraints obrigatórias.
- Script de data migration suporta reexecução sem duplicar lógica de domínio.
- `bash scripts/ci_checks.sh` permanece verde.

## 5) Plano de testes
- `bash scripts/ci_checks.sh`
- `php tests/Feature/StreetRelationalMigrationReadinessTest.php`
- `php -l scripts/migrate_json_to_mysql.php`

## 6) Plano de rollback
- Forçar `STREET_STORE_DRIVER=json` para retorno imediato ao modo antigo.
- Desconsiderar execução do script de data migration até validação de MySQL em ambiente alvo.
- Reverter commit da sprint caso necessário.
