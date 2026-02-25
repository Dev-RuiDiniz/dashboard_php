# Consolidação e Auditoria das Sprints (01–12) + Plano Estendido

## 1) Resumo executivo

A execução das sprints 01–12 foi concluída em modo **bootstrap técnico**. Houve evolução contínua de fundação (infra mínima, auth, domínios, exports, configurações e hardening), com rastreabilidade documental por sprint.

O estado atual é funcional para validação incremental, porém ainda **não é estado final de produção**.

---

## 2) Auditoria consolidada das sprints 01–12

| Sprint | Objetivo do plano | Status | Evidência principal | Observações |
|---|---|---|---|---|
| 01 | Auditoria/baseline/compatibilidade | ✅ Concluída | `SPRINT_01_REPORT.md` + artifacts | OpenAPI legado via extração estática |
| 02 | Setup PHP + CI + healthchecks + logs | ✅ Concluída | `SPRINT_02_REPORT.md` | Fundação mínima entregue |
| 03 | Auth + RBAC + auditoria | ✅ Concluída | `SPRINT_03_REPORT.md` | JWT + `/me` + guardas |
| 04 | Famílias + membros + crianças | ✅ Concluída | `SPRINT_04_REPORT.md` | CRUD base + validações CPF |
| 05 | Street + encaminhamentos + LGPD | ✅ Concluída | `SPRINT_05_REPORT.md` | Consentimento em conclusão |
| 06 | Entregas/eventos + regras críticas | ✅ Concluída | `SPRINT_06_REPORT.md` | bloqueio mensal + assinatura |
| 07 | Exportações | ✅ Concluída | `SPRINT_07_REPORT.md` | CSV/XLSX/PDF bootstrap |
| 08 | Equipamentos + empréstimos | ✅ Concluída | `SPRINT_08_REPORT.md` | empréstimo/devolução com status |
| 09 | Relatórios gerenciais + elegibilidade | ✅ Concluída | `SPRINT_09_REPORT.md` | summary + settings + check |
| 10 | Hardening + rollout/rollback | ✅ Concluída | `SPRINT_10_REPORT.md` + `SPRINT_10_RUNBOOK.md` | lockout básico + headers segurança |
| 11 | Persistência relacional inicial (social) | ✅ Concluída | `SPRINT_11_REPORT.md` + `database/migrations/*` | MySQL opcional + fallback JSON |
| 12 | Persistência relacional Street + data migration inicial | ✅ Concluída | `SPRINT_12_REPORT.md` + `scripts/migrate_json_to_mysql.php` | Street em MySQL opcional + script idempotente |

---

## 3) Conformidade com regras obrigatórias

### 3.1 `docs/DB_RULES_MYSQL.md`
- Sprints 11 e 12 introduziram migrations MySQL idempotentes para domínios social e street.
- Persistência JSON permanece como fallback transitório para rollout seguro.

### 3.2 `docs/SCREEN_RULES.md`
- Não houve criação/alteração de telas no escopo desta trilha backend.

### 3.3 Ordem e escopo do plano de migração
- A sequência de entregas respeitou o planejamento incremental 01→12 (com plano estendido).
- Cada sprint possui plano e relatório próprios.

---

## 4) Gaps atuais (para fechamento real do sistema)

1. **Persistência definitiva**: stores em JSON precisam migrar para banco relacional com migrations.
2. **Contratos formais de API**: OpenAPI versionado do backend PHP com compatibilidade legada.
3. **Paridade visual de exportações**: XLSX/PDF ainda em modo simplificado.
4. **Observabilidade de produção**: métricas/sLO/tracing e alertas avançados.
5. **Segurança avançada**: hardening corporativo (SAST/DAST, secrets, rotação, etc.).
6. **Cutover real**: plano de dados, execução blue/green e rollback validado em ambiente real.

---

## 5) Plano de sprints adicionais (necessárias)

> Proposta para fechamento do sistema após Sprint 10.

### Sprint 13 — Persistência relacional final + validação em banco real
- Migrar stores restantes para persistência relacional (`deliveries`, `equipment`, `settings`).
- Executar ensaio completo de data migration JSON→MySQL em ambiente de teste.
- Validar integridade e constraints equivalentes por domínio.

### Sprint 14 — Contratos de API e compatibilidade final
- Publicar OpenAPI v1 do backend PHP.
- Implementar facade/aliases de compatibilidade legada críticos.
- Adicionar contract tests de compatibilidade Python x PHP.

### Sprint 15 — Exportações de fidelidade e homologação funcional
- Evoluir engine de XLSX/PDF para paridade visual.
- Golden files e testes de snapshot de layout.
- Homologação com usuários-chave.

### Sprint 16 — Produção assistida e encerramento de migração
- Plano de cutover real (janela, comunicação, fallback).
- DR drill e testes de rollback operacional.
- Go/No-Go final e documento de encerramento da migração.

---

## 6) Critérios de aceite para encerramento definitivo

- Persistência e migrações estáveis em ambiente de produção.
- Contratos de API versionados e compatíveis.
- Exportações aprovadas por negócio (fidelidade mínima acordada).
- Observabilidade e segurança no nível operacional requerido.
- Runbook validado com evidência de rollback executável.

---

## 7) Evidências e referências

- Relatórios: `docs/sprints/SPRINT_01_REPORT.md` ... `docs/sprints/SPRINT_12_REPORT.md`
- Planos: `docs/sprints/SPRINT_01_EXECUTION.md` ... `docs/sprints/SPRINT_12_EXECUTION.md`
- Runbook: `docs/sprints/SPRINT_10_RUNBOOK.md`
- Artefatos baseline: `docs/sprints/artifacts/*`
