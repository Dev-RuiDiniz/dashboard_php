# Sprint 11 — Relatório de Execução

## 1) O que foi feito
- Criado plano operacional em `docs/sprints/SPRINT_11_EXECUTION.md`.
- Adicionada migration idempotente `database/migrations/001_create_social_core.sql` com tabelas `families`, `dependents` e `children`, incluindo PK/FK/UNIQUE e collation padrão.
- Implementado `scripts/run_migrations.php` para aplicar migrations SQL por PDO/MySQL.
- Evoluído `src/Domain/SocialStore.php` para suportar dois modos de persistência:
  - `json` (padrão, retrocompatível);
  - `mysql` por `SOCIAL_STORE_DRIVER=mysql` e variáveis `MYSQL_*`.
- Adicionado teste `tests/Feature/RelationalMigrationReadinessTest.php`.
- Atualizado `scripts/ci_checks.sh` para incluir lint e execução do teste da sprint.

## 2) O que NÃO foi feito (e por quê)
- Não foi migrado o restante dos stores para MySQL (`StreetStore`, `DeliveryStore`, `EquipmentStore`, `SettingsStore`) para manter foco do escopo Sprint 11.
- Não foi executada migration real em servidor MySQL nesta execução por ausência de instância DB provisionada no ambiente de validação.

## 3) Evidências
- `bash scripts/ci_checks.sh` → OK.
- `php tests/Feature/RelationalMigrationReadinessTest.php` → OK.
- Artefatos de migração presentes em `database/migrations/` e `scripts/run_migrations.php`.

## 4) Riscos e pendências
- Persistência relacional ainda parcial (somente domínio social mínimo).
- Faltam testes de integração contra MySQL real (constraints e concorrência).
- Próxima sprint deve expandir migração para demais domínios e iniciar data migration.

## 5) Próxima sprint: pré-requisitos
- Provisionar MySQL 8.0+ para testes de integração.
- Definir estratégia de migração incremental de dados JSON→MySQL por domínio.
- Criar suíte de testes para validar parity entre modos `json` e `mysql`.

## 6) Checklist de conformidade
- [x] Respeitei `docs/DB_RULES_MYSQL.md` (sim — migration com PK/FK/UNIQUE/charset/collation padrão).
- [x] Respeitei `docs/SCREEN_RULES.md` (sim — sem alteração/criação de telas).
- [x] Respeitei a Sprint 11 do plano estendido (sim — persistência relacional inicial).
- [x] Não criei campos/tabelas/telas inventadas (sim — tabelas do domínio já existente no sistema).
- [x] Rodei testes/lint/build (sim). Comandos: `bash scripts/ci_checks.sh`; `php tests/Feature/RelationalMigrationReadinessTest.php`.
