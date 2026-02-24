from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from sqlalchemy import create_engine, text

from app.core.config import DATA_DIR


def _sqlite_rows(path: Path, table: str) -> list[dict[str, object]]:
    if not path.exists():
        return []
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(f"SELECT * FROM {table}").fetchall()
        return [dict(row) for row in rows]


def _copy_table(conn, schema: str, table: str, rows: list[dict[str, object]], reset: bool) -> None:
    if not rows:
        return
    if reset:
        conn.execute(text(f"TRUNCATE TABLE {schema}.{table} RESTART IDENTITY CASCADE"))

    columns = list(rows[0].keys())
    column_sql = ", ".join(columns)
    values_sql = ", ".join(f":{column}" for column in columns)
    upsert_sql = f"INSERT INTO {schema}.{table} ({column_sql}) VALUES ({values_sql}) ON CONFLICT DO NOTHING"
    for row in rows:
        conn.execute(text(upsert_sql), row)


def migrate(sqlite_domain: Path, sqlite_auth: Path, postgres_url: str, reset: bool = False) -> None:
    pg_engine = create_engine(postgres_url)

    domain_tables = [
        "families",
        "dependents",
        "equipment",
        "loans",
        "food_baskets",
        "street_people",
        "street_services",
        "referrals",
        "visit_requests",
        "visit_executions",
    ]
    auth_tables = ["users", "roles", "user_roles"]

    with pg_engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS domain"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS auth"))

        for table in auth_tables:
            _copy_table(conn, "auth", table, _sqlite_rows(sqlite_auth, table), reset)
        for table in domain_tables:
            _copy_table(conn, "domain", table, _sqlite_rows(sqlite_domain, table), reset)


def main() -> None:
    parser = argparse.ArgumentParser(description="Migra dados de SQLite para PostgreSQL com schemas")
    parser.add_argument("--sqlite-domain", default=str(DATA_DIR / "app.db"))
    parser.add_argument("--sqlite-auth", default=str(DATA_DIR / "auth.db"))
    parser.add_argument("--postgres-url", required=True)
    parser.add_argument("--reset", action="store_true", help="Limpa tabelas de destino antes de copiar")
    args = parser.parse_args()

    migrate(Path(args.sqlite_domain), Path(args.sqlite_auth), args.postgres_url, reset=args.reset)
    print("Migração concluída com sucesso.")


if __name__ == "__main__":
    main()
