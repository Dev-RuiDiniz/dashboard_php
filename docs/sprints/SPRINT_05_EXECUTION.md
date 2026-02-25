# Sprint 05 — Plano Operacional de Execução

## 1) Escopo da sprint

### Entra na Sprint 05
- APIs mínimas para pessoas em situação de rua (`/street/people`).
- APIs mínimas de encaminhamentos (`/street/referrals`).
- Validação de consentimento LGPD obrigatório para conclusão de atendimento.
- Alteração de status de encaminhamento com auditoria.

### Não entra na Sprint 05
- Telas e fluxos SSR.
- Persistência relacional/migrações.
- Cobertura completa de todos os campos do legado.

## 2) Referências obrigatórias
- `AUDITORIA_E_PLANO_MIGRACAO_PYTHON_PHP_10_SPRINTS.md` (Sprint 05).
- `docs/DB_RULES_MYSQL.md`.
- `docs/SCREEN_RULES.md`.

## 3) Objetivo e backlog

### Objetivo
- Cobrir módulo social street com consentimento digital básico e evidências.

### Backlog
- CRUD mínimo `street person`.
- Fluxo básico de encaminhamento/status.
- Consentimento obrigatório na conclusão.

### Critérios de aceite
- Atendimento concluído sem consentimento deve falhar.
- Encaminhamentos devem aceitar alteração de status.
- Auditoria deve registrar eventos críticos.

## 4) Ordem de execução
1. Documento da sprint.
2. Store domínio street + consentimento.
3. Endpoints no kernel.
4. Testes automatizados.
5. Relatório final.

## 5) Checklist
- [x] Implementar store street/referrals.
- [x] Implementar endpoints `/street/people` e `/street/referrals`.
- [x] Exigir consentimento em conclusão de atendimento.
- [x] Implementar atualização de status de encaminhamento.
- [x] Registrar auditoria de eventos sensíveis.
- [x] Adicionar testes automatizados da sprint.
- [x] Produzir `docs/sprints/SPRINT_05_REPORT.md`.

## 6) Plano de testes
- Criar street person com consentimento incompleto e `concluded=true` retorna erro.
- Criar street person com consentimento completo retorna sucesso.
- Criar encaminhamento para pessoa existente retorna sucesso.
- Alterar status do encaminhamento retorna sucesso.
- Perfil sem permissão de escrita recebe `403`.

## 7) Rollback
- Reverter commit da sprint.
- Sem rollback de banco (sem migrações nesta sprint).
