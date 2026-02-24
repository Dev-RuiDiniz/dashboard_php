# Deploy com Docker

Este documento descreve um fluxo simples e reproduzível para subir o **Igreja Dashboard** com Docker em produção usando PostgreSQL.

## 1) Pré-requisitos

- Docker 24+
- Docker Compose v2+

Verificações rápidas:

```bash
docker --version
docker compose version
```

## 2) Configuração de ambiente

Crie um arquivo `.env` na raiz do projeto para sobrescrever segredos e parâmetros de execução.

Exemplo mínimo:

```dotenv
APP_ENV=production
SECRET_KEY=troque-para-um-segredo-forte
COOKIE_SECURE=false
POSTGRES_DB=igreja_dashboard
POSTGRES_USER=igreja_dashboard
POSTGRES_PASSWORD=troque-essa-senha
DATABASE_URL=postgresql+psycopg://igreja_dashboard:troque-essa-senha@db:5432/igreja_dashboard
DEFAULT_ADMIN_NAME=Administrador
DEFAULT_ADMIN_EMAIL=admin@example.com
DEFAULT_ADMIN_PASSWORD=troque-essa-senha
MIN_PASSWORD_LENGTH=8
```

> Em ambiente com HTTPS, configure `COOKIE_SECURE=true`.

## 3) Subir a aplicação

Na raiz do repositório:

```bash
docker compose up -d --build
```

Após subir, acesse:

- Aplicação: `http://localhost:8000`

## 4) Estado e persistência de dados

O `docker-compose.yml` sobe um PostgreSQL dedicado (`service: db`) com volume nomeado `igreja_dashboard_postgres_data`.

- Banco padrão de produção: PostgreSQL (`DATABASE_URL` apontando para `db:5432`).
- Segregação lógica por schema:
  - `domain`: famílias, dependentes, equipamentos, cestas, rua e visitas.
  - `auth`: usuários, roles e relacionamentos RBAC.
- As migrações Alembic criam schemas e estruturas automaticamente no startup do `web`.

## 5) Migrações

As migrações rodam automaticamente no startup do serviço `web` com:

```bash
alembic upgrade head
```

Se precisar executar manualmente:

```bash
docker compose exec web alembic upgrade head
```

## 6) Backup e restore (PostgreSQL)

### Backup lógico

```bash
docker compose exec db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc > /tmp/igreja_dashboard.dump'
docker cp igreja_dashboard_db:/tmp/igreja_dashboard.dump ./backups/igreja_dashboard.dump
```

### Restore lógico

```bash
docker cp ./backups/igreja_dashboard.dump igreja_dashboard_db:/tmp/igreja_dashboard.dump
docker compose exec db sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists /tmp/igreja_dashboard.dump'
```

## 7) Migração opcional de dados legados (SQLite -> PostgreSQL)

Se houver `data/app.db` e `data/auth.db` antigos:

```bash
PYTHONPATH=src python scripts/migrate_sqlite_to_postgres.py \
  --postgres-url "$DATABASE_URL"
```

Use `--reset` para limpar tabelas de destino antes de copiar.

## 8) Atualização de versão

Sempre que houver mudança de código/dependências:

```bash
docker compose up -d --build
```

## 9) Checklist rápido de produção

- `SECRET_KEY` forte e armazenada em cofre de segredos.
- `DEFAULT_ADMIN_PASSWORD` alterada para valor forte.
- `COOKIE_SECURE=true` quando HTTPS estiver ativo.
- Rotina de backup e teste de restore validada (`pg_dump`/`pg_restore`).
- Logs monitorados.

Para hardening completo, consulte `docs/producao_hardening.md`.
