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
