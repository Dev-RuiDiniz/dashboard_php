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

> **Status atual:** Sprints 01–19 concluídas em modo bootstrap técnico. As Sprints 11–19 consolidaram persistência relacional incremental, contrato OpenAPI v1, reconciliação, postura de segurança e dry-run de decisão de cutover.

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

## 6) Persistência e migrations (Sprints 11 a 13)

### Modos de persistência
- `SOCIAL_STORE_DRIVER=json|mysql` para `SocialStore`;
- `STREET_STORE_DRIVER=json|mysql` para `StreetStore`;
- `DELIVERY_STORE_DRIVER=json|mysql` para `DeliveryStore`;
- `EQUIPMENT_STORE_DRIVER=json|mysql` para `EquipmentStore`;
- `SETTINGS_STORE_DRIVER=json|mysql` para `SettingsStore`;
- por padrão todos usam `json` e podem ser migrados incrementalmente para MySQL.

### Executar migrations
```bash
php scripts/run_migrations.php
php scripts/migrate_json_to_mysql.php
php scripts/reconciliation_report.php
php scripts/security_posture_report.php
php scripts/pilot_cutover_dry_run.php
```

Variáveis suportadas:
- `MYSQL_DSN` (opcional, prioridade máxima)
- `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_CHARSET`

---

## 7) Testes automatizados atuais

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
- `RelationalMigrationReadinessTest`
- `StreetRelationalMigrationReadinessTest`
- `RemainingDomainsRelationalReadinessTest`
- `OpenApiContractTest`
- `ReportsExportFidelityTest`
- `ReconciliationReportTest`
- `SecurityPostureReportTest`
- `PilotCutoverDryRunTest`

Execução:
```bash
bash scripts/ci_checks.sh
```

---

## 8) Documentação de sprints e auditoria

- Planos/relatórios: `docs/sprints/SPRINT_01_*` até `SPRINT_19_*`.
- Runbook Sprint 10: `docs/sprints/SPRINT_10_RUNBOOK.md`.
- Runbook final Sprint 16: `docs/sprints/SPRINT_16_RUNBOOK.md`.
- Inventário legado: `docs/sprints/artifacts/INVENTORY_SPRINT01.md`.
- Snapshot OpenAPI legado (estático): `docs/sprints/artifacts/openapi_legacy_sprint01.json`.
- Matriz de compatibilidade: `docs/sprints/artifacts/COMPATIBILITY_MATRIX_SPRINT01.md`.
- OpenAPI PHP v1: `docs/sprints/artifacts/openapi_php_v1.json`.
- Golden exports: `docs/sprints/artifacts/golden_exports/*`.

---

## 9) Limitações conhecidas (bootstrap)

- persistência relacional opcional já disponível para social/street/delivery/equipment/settings;
- exportadores XLSX/PDF simplificados;
- ausência de dashboard visual no frontend;
- ausência de cutover real de produção neste repositório.

---

## 10) Próximos passos

Ver relatório consolidado e plano estendido em:
- `docs/sprints/SPRINTS_CONSOLIDATED_AUDIT_AND_NEXT_PLAN.md`


---

## 11) Configuração de ambiente

Variáveis principais:
- `JWT_SECRET` (obrigatória em ambientes reais)
- `APP_READY` (`true`/`false`)
- `MYSQL_DSN` (opcional)
- `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_CHARSET`
- `SOCIAL_STORE_DRIVER`, `STREET_STORE_DRIVER`, `DELIVERY_STORE_DRIVER`, `EQUIPMENT_STORE_DRIVER`, `SETTINGS_STORE_DRIVER`

Exemplo local (bash):
```bash
export JWT_SECRET='change-me'
export SOCIAL_STORE_DRIVER='json'
export STREET_STORE_DRIVER='json'
```

---

## 12) Fluxo recomendado de migração de dados (staging/prod)

1. Aplicar schema:
```bash
php scripts/run_migrations.php
```
2. Migrar dados do fallback JSON:
```bash
php scripts/migrate_json_to_mysql.php
php scripts/reconciliation_report.php
php scripts/security_posture_report.php
php scripts/pilot_cutover_dry_run.php
```
3. Executar validação:
```bash
bash scripts/ci_checks.sh
```
4. Executar smoke funcional por domínio (health/auth/reports/settings).

---

## 13) Relatórios de consolidação

- Auditoria consolidada: `docs/sprints/SPRINTS_CONSOLIDATED_AUDIT_AND_NEXT_PLAN.md`
- Relatório mestre: `docs/sprints/SPRINTS_MASTER_CONSOLIDATION_REPORT.md`
