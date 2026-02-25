# Sprint 08 — Plano Operacional de Execução

## 1) Escopo da sprint

### Entra na Sprint 08
- CRUD mínimo de equipamentos.
- Fluxo de empréstimo/devolução.
- Regras de transição de status (`disponivel`, `emprestado`, `manutencao`).
- Histórico básico auditável de empréstimos.

### Não entra na Sprint 08
- Telas/UX.
- Migração/schema.
- Alertas avançados (ex.: vencimento) fora do mínimo da sprint.

## 2) Referências obrigatórias
- `AUDITORIA_E_PLANO_MIGRACAO_PYTHON_PHP_10_SPRINTS.md` (Sprint 08).
- `docs/DB_RULES_MYSQL.md`.
- `docs/SCREEN_RULES.md`.

## 3) Checklist
- [x] Implementar store de equipamentos/empréstimos.
- [x] Expor endpoints de equipamentos.
- [x] Expor endpoints de empréstimo/devolução.
- [x] Garantir transições válidas de status.
- [x] Adicionar testes automatizados.
- [x] Produzir `docs/sprints/SPRINT_08_REPORT.md`.
