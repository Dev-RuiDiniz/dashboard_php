# Sprint 06 — Plano Operacional de Execução

## 1) Escopo da sprint

### Entra na Sprint 06
- APIs mínimas de eventos de entrega e convidados.
- Bloqueio de duplicidade de retirada por família no mesmo mês.
- Geração automática de código de retirada por evento.
- Registro de retirada com confirmação/assinatura simples.

### Não entra na Sprint 06
- Telas SSR/UX.
- Persistência relacional/migrações.
- Exportações PDF/Excel da Sprint 07.

## 2) Referências obrigatórias
- `AUDITORIA_E_PLANO_MIGRACAO_PYTHON_PHP_10_SPRINTS.md` (Sprint 06).
- `docs/DB_RULES_MYSQL.md`.
- `docs/SCREEN_RULES.md`.

## 3) Objetivo e backlog
- Objetivo: migrar núcleo de entregas/eventos com regras críticas.
- Backlog:
  - eventos;
  - convites;
  - retirada com assinatura;
  - bloqueio de duplicidade por mês.

## 4) Checklist
- [x] Implementar store de eventos/convites/retiradas.
- [x] Implementar endpoints `/deliveries/events` e operações de convite/retirada.
- [x] Aplicar bloqueio de duplicidade por família/mês.
- [x] Gerar código de retirada automático.
- [x] Exigir confirmação/assinatura de retirada.
- [x] Adicionar testes automatizados da sprint.
- [x] Produzir `docs/sprints/SPRINT_06_REPORT.md`.
