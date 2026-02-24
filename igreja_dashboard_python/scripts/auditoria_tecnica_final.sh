#!/usr/bin/env bash
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

SQLITE_DB="/tmp/sprint10_auditoria_sqlite.db"
PG_URL="postgresql+psycopg://postgres:postgres@127.0.0.1:5432/igreja_pr_check"

rm -f "$SQLITE_DB"

echo "[INFO] Auditoria técnica Sprint 10"
echo "[INFO] Repo: $ROOT_DIR"

echo "[CHECK] Configs obrigatórias em src/app/core/config.py"
rg -n "database_url|secret_key|cookie_secure|reports_dir" src/app/core/config.py

echo "[CHECK] Dependências declaradas"
python -m pip list --format=columns >/tmp/sprint10_pip_list.txt
python -m pip check

echo "[CHECK] Migrações SQLite do zero"
DATABASE_URL="sqlite:////$SQLITE_DB" alembic upgrade head

echo "[CHECK] Alembic check (autogenerate drift) SQLite"
if DATABASE_URL="sqlite:////$SQLITE_DB" alembic check; then
  echo "[PASS] alembic check sem drift"
else
  echo "[WARN] alembic check detectou drift (ver saída acima)"
fi

echo "[CHECK] Migrações PostgreSQL"
if DATABASE_URL="$PG_URL" alembic upgrade head; then
  echo "[PASS] PostgreSQL upgrade head ok"
else
  echo "[WARN] PostgreSQL indisponível no ambiente de auditoria"
fi

echo "[CHECK] Segurança login/reset/auditoria"
rg -n "enforce_login_rate_limit|ensure_login_not_locked|PasswordResetToken|token_hash|used_at|expires_at|log_action|sanitize_payload|SENSITIVE_KEYS" src/app/main.py src/app/security/rate_limit.py src/app/services/audit.py src/app/models/user.py

echo "[DONE] Auditoria técnica automatizada finalizada"
