# dashboard_php

Backend bootstrap em PHP para migração incremental do sistema social (origem Python/FastAPI), com execução orientada por sprints e rastreabilidade documental.

## 1) Visão geral

Este repositório contém:
- base HTTP em PHP (`public/index.php` + `src/Http/Kernel.php`);
- autenticação JWT e RBAC mínimo;
- domínios operacionais migrados por sprint (famílias, street, entregas, equipamentos);
- exportações (CSV/XLSX/PDF bootstrap);
- configuração/elegibilidade parametrizável;
- hardening básico (lockout + headers de segurança);
- documentação de execução e relatórios de sprints.

> **Status atual:** o plano de 10 sprints foi concluído em modo bootstrap técnico, com pendências conhecidas para produção (persistência definitiva, paridade visual final de exports, validação estatística A/B e hardening avançado).

---

## 2) Estrutura do projeto

- `public/index.php` — entrypoint HTTP.
- `src/Http/Kernel.php` — roteamento e regras de aplicação.
- `src/Auth/*` — JWT + usuários bootstrap.
- `src/Domain/*` — stores/serviços por domínio (social, street, deliveries, equipment, settings, throttle).
- `src/Reports/*` — exportadores.
- `tests/Feature/*` — testes de integração simplificada por script.
- `scripts/ci_checks.sh` — lint + execução das suítes.
- `.github/workflows/php-ci.yml` — execução CI no GitHub Actions.
- `docs/sprints/*` — planos/relatórios de sprint e artefatos de auditoria.

---

## 3) Como executar localmente

### Pré-requisitos
- PHP 8.3+
- `bash`

### Rodar checks completos
```bash
bash scripts/ci_checks.sh
```

### Subir servidor local
```bash
php -S 127.0.0.1:8099 -t public
```

### Healthcheck
```bash
curl -i http://127.0.0.1:8099/health
curl -i http://127.0.0.1:8099/ready
```

---

## 4) Autenticação e perfis

### Endpoints
- `POST /auth/login`
- `GET /me`
- `POST /auth/logout`
- `GET /admin/ping`

### Usuários bootstrap (somente desenvolvimento)
- `admin@local` / `admin123`
- `operador@local` / `operador123`
- `leitura@local` / `leitura123`

### Hardening de login (Sprint 10)
- lockout básico por tentativas inválidas (resposta `429`);
- headers de segurança aplicados no entrypoint:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: no-referrer`
  - `Content-Security-Policy: default-src 'none'; frame-ancestors 'none';`

---

## 5) APIs por domínio

### Social base (Sprint 04)
- `GET/POST /families`
- `GET/PUT/DELETE /families/{id}`
- `GET/POST /dependents`
- `DELETE /dependents/{id}`
- `GET/POST /children`
- `DELETE /children/{id}`

Regras-chave:
- validação de CPF de responsável;
- bloqueio de CPF duplicado;
- integridade de vínculo `family_id`.

### Street + LGPD (Sprint 05)
- `GET/POST /street/people`
- `POST /street/referrals`
- `POST /street/referrals/{id}/status`

Regra-chave:
- conclusão de atendimento exige `consent_accepted=true` e `signature_name`.

### Entregas/Eventos (Sprint 06)
- `GET/POST /deliveries/events`
- `POST /deliveries/events/{id}/invites`
- `POST /deliveries/events/{id}/withdrawals`

Regras-chave:
- bloqueio de retirada duplicada por família no mesmo mês;
- retirada exige assinatura;
- convite gera `withdrawal_code` automático (6 chars).

### Equipamentos/Empréstimos (Sprint 08)
- `GET/POST /equipment`
- `PUT /equipment/{id}`
- `GET/POST /equipment/loans`
- `POST /equipment/loans/{id}/return`

Status suportados:
- `disponivel`, `emprestado`, `manutencao`

### Relatórios/Configurações (Sprint 07 + 09)
- `GET /reports/export.csv`
- `GET /reports/export.xlsx`
- `GET /reports/export.pdf`
- `GET /reports/summary`
- `GET/PUT /settings/eligibility`
- `POST /eligibility/check`

---

## 6) Testes automatizados atuais

Suites em `tests/Feature/`:
- `HealthReadyTest`
- `AuthRbacAuditTest`
- `FamilyDomainCrudTest`
- `StreetLgpdReferralTest`
- `DeliveryEventsRulesTest`
- `ReportsExportTest`
- `EquipmentLoansTest`
- `ReportsEligibilitySettingsTest`
- `SecurityHardeningTest`

Execução:
```bash
bash scripts/ci_checks.sh
```

---

## 7) Documentação de sprints e auditoria

- Planos/relatórios: `docs/sprints/SPRINT_01_*` até `SPRINT_10_*`.
- Runbook Sprint 10: `docs/sprints/SPRINT_10_RUNBOOK.md`.
- Inventário legado: `docs/sprints/artifacts/INVENTORY_SPRINT01.md`.
- Snapshot OpenAPI legado (estático): `docs/sprints/artifacts/openapi_legacy_sprint01.json`.
- Matriz de compatibilidade: `docs/sprints/artifacts/COMPATIBILITY_MATRIX_SPRINT01.md`.

---

## 8) Limitações conhecidas (bootstrap)

- persistência em JSON (não relacional);
- exportadores XLSX/PDF simplificados;
- ausência de dashboard visual no frontend;
- ausência de cutover real de produção neste repositório.

---

## 9) Próximos passos

Ver relatório consolidado e plano estendido em:
- `docs/sprints/SPRINTS_CONSOLIDATED_AUDIT_AND_NEXT_PLAN.md`
