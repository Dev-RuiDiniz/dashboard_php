# Sprint 14 — Plano Operacional de Execução

## 1) Escopo da sprint

### Entra na Sprint 14
- Publicar contrato OpenAPI v1 do backend PHP em artefato versionado.
- Adicionar teste automatizado de contrato para validar paths/métodos essenciais.
- Atualizar documentação de sprints e README com referência ao contrato v1.

### Não entra na Sprint 14
- Mudança de endpoints de negócio.
- Mudança de telas/UX.
- Refatoração de arquitetura HTTP.

## 2) Referências obrigatórias
- `docs/DB_RULES_MYSQL.md`.
- `docs/SCREEN_RULES.md`.
- `docs/sprints/SPRINTS_CONSOLIDATED_AUDIT_AND_NEXT_PLAN.md` (Sprint 14).

## 3) Checklist
- [x] Criar `docs/sprints/artifacts/openapi_php_v1.json`.
- [x] Adicionar teste de contrato (`OpenApiContractTest`).
- [x] Atualizar `scripts/ci_checks.sh`.
- [x] Atualizar documentação de sprint e consolidado.
- [x] Produzir `docs/sprints/SPRINT_14_REPORT.md`.

## 4) Critérios de aceite
- OpenAPI v1 válido em JSON e versionado no repositório.
- Teste de contrato verifica endpoints críticos já existentes no Kernel.
- Pipeline local continua verde.

## 5) Plano de testes
- `bash scripts/ci_checks.sh`
- `php tests/Feature/OpenApiContractTest.php`
- `python -m json.tool docs/sprints/artifacts/openapi_php_v1.json`

## 6) Plano de rollback
- Remover artefato OpenAPI v1 e teste de contrato caso incompatibilidade crítica seja encontrada.
- Não há impacto de schema ou contrato runtime nesta sprint (somente formalização de contrato).
