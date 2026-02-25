# Sprint 01 — Plano Operacional de Execução

## 1) Escopo da sprint

### Entra na Sprint 01
- Congelar inventário técnico **as-is** de endpoints e entidades do backend atual.
- Gerar snapshot de contrato OpenAPI legado.
- Consolidar matriz de compatibilidade Python atual → alvo PHP.
- Classificar gaps com status `OK | Parcial | Ausente | Divergente`.
- Registrar baseline operacional inicial (smoke + linha de base de latência/erros disponível no ambiente local).

### Não entra na Sprint 01
- Implementação de novo backend PHP/Laravel (previsto para Sprint 02+).
- Alterações de schema/tabelas e migrações de banco.
- Criação/alteração de telas, rotas de UX ou campos de formulário.
- Mudanças funcionais de negócio.

## 2) Fontes e regras de referência obrigatórias
- Plano macro de migração: `AUDITORIA_E_PLANO_MIGRACAO_PYTHON_PHP_10_SPRINTS.md` (Sprint 1).
- Constituição de banco: `docs/DB_RULES_MYSQL.md`.
- Constituição de telas/UX: `docs/SCREEN_RULES.md`.

## 3) Objetivo, backlog e critérios de aceite (extraído do plano)

### Objetivo da Sprint 01
- Fechar inventário técnico e contratos “as-is”.

### Itens obrigatórios
- Congelar mapa de endpoints e entidades.
- Gerar OpenAPI legado.
- Definir matriz de compatibilidade e riscos.

### Critérios de aceite
- Inventário aprovado por produto/tech lead.
- Gaps classificados (`OK/Parcial/Ausente/Divergente`).

### Testes obrigatórios
- Smoke no backend atual.
- Snapshot de contratos.

### Observabilidade mínima
- Baseline de erro/latência atual (p95) quando tecnicamente possível no ambiente.

### Entregáveis
- Relatório de auditoria.
- Backlog priorizado.

## 4) Dependências e ordem de execução

### Dependências
- Ambiente Python funcional para inspeção de rotas e geração do contrato OpenAPI.
- Código-fonte FastAPI atual acessível (`igreja_dashboard_python`).
- Ferramentas locais de validação (ex.: `pytest`) conforme disponibilidade.

### Ordem operacional (seguindo o guia do projeto)
1. **Documentação**: produzir este plano de execução.
2. **Base técnica mínima Sprint 01**: extrair inventário e contrato legado.
3. **Backend (somente auditoria)**: mapear endpoints/entidades e compatibilidade.
4. **Front**: não aplicável nesta sprint (sem criação/alteração de telas).
5. **Testes + relatório final**: smoke/snapshot e relatório da sprint.

## 5) Checklist de tarefas
- [x] Extrair lista de rotas/endpoints do backend legado.
- [x] Extrair entidades principais do domínio atual.
- [x] Gerar snapshot OpenAPI legado para rastreabilidade.
- [x] Consolidar matriz de compatibilidade de APIs legadas.
- [x] Classificar gaps (OK/Parcial/Ausente/Divergente).
- [x] Rodar smoke tests do backend atual.
- [x] Produzir relatório da sprint em `docs/sprints/SPRINT_01_REPORT.md`.

## 6) Critérios de aceite operacionais desta execução
- [ ] Existe snapshot OpenAPI versionado dentro do repositório.
- [ ] Existe inventário técnico de endpoints e entidades.
- [ ] Existe matriz de compatibilidade consolidada e riscos da Sprint 01.
- [ ] Existe evidência de smoke test local.
- [ ] Não houve criação de tela, campo, endpoint funcional novo ou alteração de schema.

## 7) Plano de testes
- Validar consistência mínima com:
  - execução de testes automatizados existentes (`pytest`);
  - geração do snapshot OpenAPI via import do app FastAPI;
  - checagem de integridade JSON do snapshot (`python -m json.tool`).

## 8) Plano de rollback
Como Sprint 01 é de baseline e documentação:
- rollback = reverter commit da sprint;
- remover artefatos gerados de inventário/snapshot caso necessário;
- não há rollback de banco/telas porque não haverá mudança funcional.
