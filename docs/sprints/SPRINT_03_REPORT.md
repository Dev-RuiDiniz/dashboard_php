# Sprint 03 — Relatório de Execução

## 1) O que foi feito
- Criado plano operacional da Sprint 03 em `docs/sprints/SPRINT_03_EXECUTION.md`.
- Implementado JWT HS256 (emissão/validação) em `src/Auth/JwtService.php`.
- Implementado store de usuários/roles/permissões para bootstrap em `src/Auth/UserStore.php`.
- Implementado auditoria de eventos sensíveis em `src/Audit/AuditLogger.php`.
- Evoluído kernel HTTP com:
  - `POST /auth/login`
  - `GET /me`
  - `POST /auth/logout`
  - `GET /admin/ping` (rota protegida Admin para validação RBAC)
  em `src/Http/Kernel.php`.
- Atualizado `public/index.php` para parse de payload JSON e ligação de auditoria.
- Adicionado teste de auth + RBAC + auditoria em `tests/Feature/AuthRbacAuditTest.php`.
- Mantido e ajustado teste de health/readiness em `tests/Feature/HealthReadyTest.php`.
- Atualizado script de checks em `scripts/ci_checks.sh`.

## 2) O que NÃO foi feito (e por quê)
- Não foi implementado CRUD persistente de usuários/roles/permissões (fora do escopo da Sprint 03; foco em paridade inicial de auth/RBAC).
- Não foi implementado lockout/rate-limit avançado (hardening futuro).
- Não houve alteração de banco/schema/migrations.
- Não houve criação/alteração de telas.

## 3) Evidências
- `bash scripts/ci_checks.sh` → OK.
- `POST /auth/login` com credenciais válidas retorna token.
- `GET /me` com Bearer token válido retorna dados do usuário.
- `GET /admin/ping` com token de operador retorna `403`.
- Teste automatizado confirma auditoria para `auth.login_failed`, `auth.login_success`, `auth.forbidden`, `auth.logout`.

## 4) Riscos e pendências
- Usuários em memória são apenas bootstrap técnico; necessário persistir em banco na evolução do módulo de usuários.
- Logout atual é técnico/auditável e não invalida token (modelo stateless); política de revogação deve ser definida.
- Necessário alinhar matriz de permissões completa com catálogo legado na próxima evolução de auth.

## 5) Próxima sprint — pré-requisitos
- Evoluir para módulo de domínio planejado na sprint subsequente, mantendo guardas RBAC.
- Definir persistência de usuários/roles/permissões e trilha auditável com storage real.

## 6) Checklist de conformidade
- [x] Respeitei `docs/DB_RULES_MYSQL.md` (sim — sem mudança de schema/migração).
- [x] Respeitei `docs/SCREEN_RULES.md` (sim — sem novas telas/fluxos).
- [x] Respeitei a Sprint 3 do plano (sim — JWT, `/me`, RBAC e auditoria inicial).
- [x] Não criei campos/tabelas/telas inventadas (sim).
- [x] Rodei testes/lint/build (sim). Comandos: `bash scripts/ci_checks.sh`; `php -S 127.0.0.1:8112 -t public`; `curl` para `/auth/login`, `/me`, `/admin/ping`.
