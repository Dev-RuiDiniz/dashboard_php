# Sprint 13 — Relatório de Execução

## 1) O que foi feito
- Criado plano da sprint em `docs/sprints/SPRINT_13_EXECUTION.md`.
- Criada migration `database/migrations/003_create_delivery_equipment_settings_core.sql` para:
  - `delivery_events`, `delivery_invites`, `delivery_withdrawals`
  - `equipments`, `equipment_loans`
  - `eligibility_settings`
- Evoluídos os stores para modo dual (JSON/MySQL):
  - `src/Domain/DeliveryStore.php`
  - `src/Domain/EquipmentStore.php`
  - `src/Domain/SettingsStore.php`
- Expandido `scripts/migrate_json_to_mysql.php` para migrar dados de `delivery_store.json`, `equipment_store.json` e `settings_store.json`.
- Adicionado teste `tests/Feature/RemainingDomainsRelationalReadinessTest.php`.
- Atualizado `scripts/ci_checks.sh` com lint e execução da nova suíte.

## 2) O que NÃO foi feito (e por quê)
- Não foi executado ensaio real em MySQL nesta execução por indisponibilidade de instância DB no ambiente.
- Não foi realizada validação de performance/volume da data migration (depende ambiente de staging com massa representativa).

## 3) Evidências
- `bash scripts/ci_checks.sh` → OK.
- `php tests/Feature/RemainingDomainsRelationalReadinessTest.php` → OK.
- Artefatos de migration e script idempotente atualizados em `database/migrations/` e `scripts/`.

## 4) Riscos e pendências
- Necessário validar constraints e integridade em banco real com massa representativa.
- Migração de dados demanda checklist operacional e reconciliação por domínio.
- Próxima sprint deve focar OpenAPI/compatibilidade de contrato e testes de contrato.

## 5) Próxima sprint: pré-requisitos
- Provisionar MySQL 8.0+ em ambiente de teste/homologação.
- Executar run completo de migrations + data migration.
- Definir baseline de contrato OpenAPI v1 e plano de contract tests.

## 6) Checklist de conformidade
- [x] Respeitei `docs/DB_RULES_MYSQL.md` (sim — migrations com PK/FK/UNIQUE/índices/charset/collation).
- [x] Respeitei `docs/SCREEN_RULES.md` (sim — sem mudança de telas).
- [x] Respeitei a Sprint 13 do plano estendido (sim — persistência relacional final dos stores + data migration).
- [x] Não criei campos/tabelas/telas inventadas (sim — tabelas aderentes aos domínios existentes).
- [x] Rodei testes/lint/build (sim). Comandos: `bash scripts/ci_checks.sh`; `php tests/Feature/RemainingDomainsRelationalReadinessTest.php`.
