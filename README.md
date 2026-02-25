# dashboard_php

## Bootstrap PHP (Sprint 02)

Estrutura técnica inicial para migração:

- Entrada HTTP: `public/index.php`
- Endpoints técnicos: `GET /health`, `GET /ready`
- Observabilidade: `request_id` + log JSON por requisição
- CI inicial: `.github/workflows/php-ci.yml`

### Rodar checks locais

```bash
bash scripts/ci_checks.sh
```

### Subir servidor local

```bash
php -S 127.0.0.1:8099 -t public
```


### Endpoints técnicos de autenticação (Sprint 03)

- `POST /auth/login`
- `GET /me`
- `POST /auth/logout`

Credenciais de bootstrap (somente ambiente de desenvolvimento):

- `admin@local` / `admin123`
- `operador@local` / `operador123`
- `leitura@local` / `leitura123`


### Endpoints de domínio social (Sprint 04)

- `GET/POST /families`
- `GET/PUT/DELETE /families/{id}`
- `GET/POST /dependents`
- `DELETE /dependents/{id}`
- `GET/POST /children`
- `DELETE /children/{id}`


### Endpoints social street (Sprint 05)

- `GET/POST /street/people`
- `POST /street/referrals`
- `POST /street/referrals/{id}/status`

Regra LGPD aplicada: conclusão de atendimento exige `consent_accepted=true` e `signature_name`.


### Endpoints entregas/eventos (Sprint 06)

- `GET/POST /deliveries/events`
- `POST /deliveries/events/{id}/invites`
- `POST /deliveries/events/{id}/withdrawals`

Regras críticas:
- bloqueio de retirada duplicada no mesmo mês por família;
- retirada exige assinatura simples (`signature_accepted` + `signature_name`);
- convite gera `withdrawal_code` automático (6 chars).


### Endpoints de exportação (Sprint 07)

- `GET /reports/export.csv`
- `GET /reports/export.xlsx`
- `GET /reports/export.pdf`

Observação: no bootstrap técnico, XLSX e PDF são versões simplificadas para validação incremental dos fluxos de exportação.
