# Sprint 03 — Plano Operacional de Execução

## 1) Escopo da sprint

### Entra na Sprint 03
- Autenticação JWT com endpoints:
  - `POST /auth/login`
  - `GET /me`
  - `POST /auth/logout`
- Base de usuários/roles/permissões em memória para bootstrap de compatibilidade.
- RBAC mínimo com papéis padrão `Admin`, `Operador`, `Leitura`.
- Trilha de auditoria para eventos sensíveis de autenticação/autorização.

### Não entra na Sprint 03
- CRUD completo de usuários com persistência em banco.
- Gestão de permissões por UI.
- Lockout/rate-limit avançado (futuro hardening).
- Alterações de telas e de schema/migrações.

## 2) Referências obrigatórias
- `AUDITORIA_E_PLANO_MIGRACAO_PYTHON_PHP_10_SPRINTS.md` (Sprint 03).
- `docs/DB_RULES_MYSQL.md`.
- `docs/SCREEN_RULES.md`.

## 3) Objetivo e backlog da Sprint 03

### Objetivo
- Reproduzir núcleo inicial de segurança (JWT + RBAC + auditoria) em stack PHP.

### Backlog obrigatório
- Login JWT.
- Endpoint autenticado `/me`.
- Logout técnico.
- Matriz de papéis/permissões base.
- Auditoria de eventos sensíveis.

### Critérios de aceite
- Login com credenciais válidas gera token.
- `/me` responde dados do usuário autenticado.
- Permissões/roles são validadas para acesso a recurso protegido.
- Eventos de login e negação de acesso são auditáveis.

## 4) Ordem de execução
1. Documento de execução da sprint.
2. Serviço de JWT + store de usuários/roles/permissões.
3. Endpoints `/auth/login`, `/me`, `/auth/logout`.
4. Camada de auditoria dos eventos sensíveis.
5. Testes automatizados.
6. Relatório final da sprint.

## 5) Checklist
- [x] Implementar JWT (criação e validação).
- [x] Implementar `POST /auth/login`.
- [x] Implementar `GET /me` com token Bearer.
- [x] Implementar `POST /auth/logout`.
- [x] Implementar validação RBAC mínima.
- [x] Implementar auditoria de login e acesso negado.
- [x] Adicionar testes automatizados da sprint.
- [x] Produzir `docs/sprints/SPRINT_03_REPORT.md`.

## 6) Plano de testes
- Login válido retorna `200` com token JWT.
- Login inválido retorna `401`.
- `/me` sem token retorna `401`.
- `/me` com token válido retorna `200`.
- Endpoint protegido para Admin retorna `403` para usuário sem papel.
- Auditoria registra eventos de login e de negação de acesso.

## 7) Rollback
- Reverter commit da sprint.
- Remover artefatos da Sprint 03 se necessário.
- Sem rollback de banco (sem migração nesta sprint).
