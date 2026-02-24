from __future__ import annotations

import argparse
import logging
import sys

from app.db.reset import run_reset


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ferramentas operacionais do Igreja Dashboard")
    subparsers = parser.add_subparsers(dest="command")

    db_parser = subparsers.add_parser("db", help="Operações de banco de dados")
    db_subparsers = db_parser.add_subparsers(dest="db_command")

    reset_parser = db_subparsers.add_parser("reset", help="Drop total + migrações + seed + validações")
    reset_parser.add_argument(
        "--keep-legacy-sqlite",
        action="store_true",
        help="Não remove arquivos SQLite legados em ./data",
    )

    return parser


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "db" and args.db_command == "reset":
        run_reset(remove_legacy_sqlite=not args.keep_legacy_sqlite)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
