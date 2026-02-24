# Hardening de produção

Este guia consolida o baseline de segurança operacional para subir o **Igreja Dashboard** em produção.

## 1) Auditoria completa (pré-go-live)

Checklist recomendado:

- [ ] `SECRET_KEY` forte e rotacionável em cofre de segredos.
- [ ] Usuário admin inicial alterado e sem senha padrão.
- [ ] `COOKIE_SECURE=true` quando HTTPS estiver ativo.
- [ ] Banco PostgreSQL com backup agendado e restore validado.
- [ ] Logs estruturados habilitados com retenção e monitoração.
- [ ] Migrações aplicadas (`alembic upgrade head`) antes do deploy.
- [ ] Testes automatizados executados no pipeline.
- [ ] `DATABASE_URL` apontando para PostgreSQL em produção (sem SQLite).

## 2) Logs estruturados

A aplicação já emite logs estruturados JSON por padrão (`LOG_JSON=true`) incluindo:

- `request_id`
- `method`
- `path`
- `status_code`
- `duration_ms`
- `client_ip`
- `user_id`
- `app_env`

Use `X-Request-ID` no request para correlação ponta-a-ponta (se omitido, o sistema gera automaticamente).

## 3) Banco e schemas

Em produção, utilizar banco único PostgreSQL com dois schemas:

- `auth` para autenticação e RBAC.
- `domain` para dados de negócio.

A criação de schemas é idempotente e controlada por migração Alembic.

## 4) Backup e restore (PostgreSQL)

### Backup

```bash
pg_dump -U <usuario> -d <database> -Fc > igreja_dashboard.dump
```

### Restore

```bash
pg_restore -U <usuario> -d <database> --clean --if-exists igreja_dashboard.dump
```

### Teste obrigatório de restore

Faça restore periódico em ambiente de homologação e valide login/RBAC, CRUD de domínio e relatórios/exportação.
