# Sprint 11 — Plano Operacional de Execução

## 1) Escopo da sprint

### Entra na Sprint 11
- Iniciar migração da persistência de `SocialStore` para modo relacional (MySQL) mantendo fallback JSON.
- Adicionar migrations SQL idempotentes para `families`, `dependents` e `children` em conformidade com `DB_RULES_MYSQL`.
- Adicionar utilitário de aplicação de migrations via PDO (ambiente local/CI externo).
- Adicionar teste automatizado mínimo de prontidão da migração relacional.

### Não entra na Sprint 11
- Migração completa de todos os domínios (`street`, `deliveries`, `equipment`, `settings`) para MySQL.
- Data migration legada Python→PHP em produção.
- Alteração de telas/UX (fora de `SCREEN_RULES`).

## 2) Referências obrigatórias
- `AUDITORIA_E_PLANO_MIGRACAO_PYTHON_PHP_10_SPRINTS.md` (continuidade pós Sprint 10 conforme plano estendido).
- `docs/sprints/SPRINTS_CONSOLIDATED_AUDIT_AND_NEXT_PLAN.md` (Sprint 11 proposta).
- `docs/DB_RULES_MYSQL.md`.
- `docs/SCREEN_RULES.md`.

## 3) Checklist
- [x] Criar migration SQL idempotente para domínio social mínimo (`families/dependents/children`).
- [x] Implementar `SocialStore` com suporte opcional a MySQL via `SOCIAL_STORE_DRIVER=mysql`.
- [x] Criar script de execução de migrations (`scripts/run_migrations.php`).
- [x] Adicionar teste de prontidão relacional.
- [x] Atualizar pipeline local (`scripts/ci_checks.sh`).
- [x] Produzir `docs/sprints/SPRINT_11_REPORT.md`.

## 4) Critérios de aceite
- CRUD de famílias/dependentes/crianças continua funcionando no fallback JSON atual.
- SQL de migração cria tabelas com PK/FK/UNIQUE e `utf8mb4` conforme regra.
- Script de migration aplica todos os `.sql` em ordem lexical.
- Testes e lint locais passam no ambiente atual.

## 5) Plano de testes
- Executar `bash scripts/ci_checks.sh`.
- Executar teste dedicado `php tests/Feature/RelationalMigrationReadinessTest.php`.
- Validar sintaxe de migration runner: `php -l scripts/run_migrations.php`.

## 6) Plano de rollback
- Se houver falha no modo MySQL, manter `SOCIAL_STORE_DRIVER=json` para continuidade operacional.
- Reverter alterações desta sprint para restabelecer apenas persistência JSON.
- Não há alteração de contrato HTTP nesta sprint.
