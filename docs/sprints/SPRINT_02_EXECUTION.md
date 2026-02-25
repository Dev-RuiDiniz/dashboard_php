# Sprint 02 — Plano Operacional de Execução

## 1) Escopo da sprint

### Entra na Sprint 02
- Bootstrap inicial da plataforma PHP para migração.
- Entrega dos endpoints técnicos `/health` e `/ready`.
- Inclusão de `request_id` por requisição.
- Logging estruturado em JSON para observabilidade.
- Pipeline CI mínima com validação de sintaxe e testes automatizados básicos.

### Não entra na Sprint 02
- Implementação de módulos de domínio (famílias, crianças, entregas, etc.).
- Alteração de schema/tabelas/migrações de banco.
- Criação/alteração de telas e fluxos UX.
- Autenticação/RBAC (previsto na Sprint 03).

## 2) Referências obrigatórias
- `AUDITORIA_E_PLANO_MIGRACAO_PYTHON_PHP_10_SPRINTS.md` (Sprint 02).
- `docs/DB_RULES_MYSQL.md`.
- `docs/SCREEN_RULES.md`.

## 3) Objetivo e backlog da Sprint 02

### Objetivo
- Construir a fundação técnica PHP com CI, healthchecks e observabilidade mínima.

### Backlog obrigatório
- Bootstrap PHP.
- Pipeline CI (lint + testes).
- Middleware/propagação de `request_id`.
- Endpoints `/health` e `/ready`.

### Critérios de aceite
- Build CI verde.
- Endpoints técnicos respondendo com contrato estável.
- Logs JSON contendo `request_id`, status e latência.

## 4) Dependências e ordem de execução
1. Documentação da sprint (este arquivo).
2. Estrutura técnica base PHP + roteamento técnico.
3. Observabilidade (`request_id` + logs JSON).
4. Testes automatizados de smoke técnico.
5. CI com lint e execução dos testes.
6. Relatório final da sprint.

## 5) Checklist
- [x] Criar estrutura base PHP.
- [x] Implementar endpoint `GET /health`.
- [x] Implementar endpoint `GET /ready`.
- [x] Implementar geração/propagação de `request_id`.
- [x] Implementar logs JSON por requisição.
- [x] Adicionar testes automatizados de endpoints técnicos.
- [x] Configurar workflow de CI.
- [x] Produzir `docs/sprints/SPRINT_02_REPORT.md`.

## 6) Plano de testes
- Testes de unidade/integração leve para kernel HTTP técnico:
  - `GET /health` retorna `200` e payload esperado.
  - `GET /ready` retorna `200` quando `APP_READY=true`.
  - `GET /ready` retorna `503` quando `APP_READY=false`.
  - `request_id` é preservado quando cabeçalho é enviado.
- Lint PHP em todos os arquivos versionados.

## 7) Rollback
- Reverter commit da sprint.
- Remover artefatos de bootstrap caso necessário.
- Sem rollback de banco (sem migração nesta sprint).
