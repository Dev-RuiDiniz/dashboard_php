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
