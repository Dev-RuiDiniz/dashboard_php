# AGENTS

## PowerShell quickstart (Windows)

SQLite (DB limpo):

```powershell
$env:DATABASE_URL = "sqlite:////tmp/pr_sqlite.db"
alembic upgrade head
alembic check
```

PostgreSQL local:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/igreja_pr_check"
alembic upgrade head
alembic check
```

Se o `alembic_version` apontar para revision inexistente em DB local,
apague o SQLite local (ou recrie o banco PostgreSQL) e rode `alembic upgrade head` novamente.
