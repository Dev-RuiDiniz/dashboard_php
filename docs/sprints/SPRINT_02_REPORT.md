# Sprint 02 — Relatório de Execução

## 1) O que foi feito
- Criado plano operacional da sprint em `docs/sprints/SPRINT_02_EXECUTION.md`.
- Implementado bootstrap técnico PHP com ponto de entrada HTTP em `public/index.php`.
- Implementado kernel técnico com rotas `GET /health` e `GET /ready` em `src/Http/Kernel.php`.
- Implementado contexto de requisição para geração/propagação de `request_id` em `src/Http/RequestContext.php`.
- Implementado logging estruturado JSON de requisição em `src/Observability/JsonLogger.php`.
- Adicionado teste automatizado de smoke técnico para health/readiness em `tests/Feature/HealthReadyTest.php`.
- Adicionado script de checks locais/CI em `scripts/ci_checks.sh`.
- Adicionado workflow de CI em `.github/workflows/php-ci.yml`.

## 2) O que NÃO foi feito (e por quê)
- Não foi feito bootstrap Laravel 11 completo com dependências de framework, porque nesta etapa foi priorizada fundação mínima executável e validável sem dependências externas para cumprir os critérios técnicos da Sprint 02.
- Não foram implementados módulos funcionais (auth/RBAC/domínios) pois pertencem às próximas sprints do plano.
- Não houve alteração de banco, schema, tabelas ou migrações (fora do escopo da Sprint 02).
- Não houve criação/alteração de telas/fluxos UX (fora do escopo da Sprint 02).

## 3) Evidências (comandos e resultados)
- `bash scripts/ci_checks.sh` → **OK** (lint + teste técnico).
- `php -S 127.0.0.1:8099 -t public` + `curl -i /health` → **200 OK**.
- `APP_READY=false php -S 127.0.0.1:8100 -t public` + `curl -i /ready` → **503 Service Unavailable**.

## 4) Riscos e pendências
- Pendência para Sprint 03+: convergir bootstrap mínimo para Laravel 11 completo mantendo os mesmos contratos técnicos (`/health`, `/ready`, `request_id`, logs JSON).
- Definir padrão final de ingestão de logs (destino/stack observabilidade) para produção.
- Definir readiness com check real de dependências (ex.: banco/fila/cache) quando essas camadas forem introduzidas.

## 5) Próxima sprint (Sprint 03) — pré-requisitos
- Introduzir autenticação JWT (`/auth/login`, `/me`, logout) em stack PHP alvo.
- Introduzir matriz RBAC e trilha de auditoria para CRUD de usuários.
- Manter compatibilidade de contratos legados mapeados na Sprint 01.

## 6) Checklist de conformidade
- [x] Respeitei `docs/DB_RULES_MYSQL.md` (sim — sem mudança de schema/migração).
- [x] Respeitei `docs/SCREEN_RULES.md` (sim — sem novas telas/fluxos).
- [x] Respeitei a Sprint 2 do plano (sim — bootstrap, CI, logs, healthchecks).
- [x] Não criei campos/tabelas/telas inventadas (sim).
- [x] Rodei testes/lint/build (sim). Comandos: `bash scripts/ci_checks.sh`; `php -S 127.0.0.1:8099 -t public` + `curl -i /health`; `APP_READY=false php -S 127.0.0.1:8100 -t public` + `curl -i /ready`.
