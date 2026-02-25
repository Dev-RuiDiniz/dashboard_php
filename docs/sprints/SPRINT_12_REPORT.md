# Sprint 12 — Relatório de Execução

## 1) O que foi feito
- Criado plano operacional em `docs/sprints/SPRINT_12_EXECUTION.md`.
- Criada migration `database/migrations/002_create_street_core.sql` para `street_residents` e `street_referrals`.
- Evoluído `src/Domain/StreetStore.php` para operar em dois modos:
  - `json` (compatível com estado anterior)
  - `mysql` por `STREET_STORE_DRIVER=mysql`.
- Criado script `scripts/migrate_json_to_mysql.php` para migração idempotente dos dados `social` e `street` do JSON para MySQL.
- Adicionado teste `tests/Feature/StreetRelationalMigrationReadinessTest.php`.
- Atualizado `scripts/ci_checks.sh` com lint e execução dos novos artefatos.

## 2) O que NÃO foi feito (e por quê)
- Não foram migrados nesta sprint os módulos `deliveries`, `equipment` e `settings` para manter incrementalidade e reduzir risco de regressão.
- Não houve execução real de data migration em MySQL neste ambiente por ausência de instância provisionada.

## 3) Evidências
- `bash scripts/ci_checks.sh` → OK.
- `php tests/Feature/StreetRelationalMigrationReadinessTest.php` → OK.
- Arquivos de migração e script idempotente presentes em `database/migrations/` e `scripts/`.

## 4) Riscos e pendências
- Persistência relacional ainda parcial no sistema.
- Data migration precisa de ensaio em banco real e validação de volume.
- Próxima sprint deve cobrir os stores restantes e validação de consistência ponta-a-ponta.

## 5) Próxima sprint: pré-requisitos
- Subir MySQL 8.0+ em ambiente de teste.
- Definir checklist de verificação pós-migração por domínio.
- Expandir testes de integração real contra MySQL.

## 6) Checklist de conformidade
- [x] Respeitei `docs/DB_RULES_MYSQL.md` (sim — migration com PK/FK/índices/charset/collation).
- [x] Respeitei `docs/SCREEN_RULES.md` (sim — sem mudanças de tela).
- [x] Respeitei a Sprint 12 do plano estendido (sim — persistência relacional expandida + data migration inicial).
- [x] Não criei campos/tabelas/telas inventadas (sim — tabelas aderentes ao domínio Street existente).
- [x] Rodei testes/lint/build (sim). Comandos: `bash scripts/ci_checks.sh`; `php tests/Feature/StreetRelationalMigrationReadinessTest.php`.
