from __future__ import annotations

import argparse
from pathlib import Path

from app.core.backup import create_backup, default_backup_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera backup SQLite da aplicação.")
    parser.add_argument(
        "--destination",
        default=str(default_backup_dir()),
        help="Diretório de destino para o backup.",
    )
    args = parser.parse_args()

    path = create_backup(destination_dir=Path(args.destination))
    print(path)


if __name__ == "__main__":
    main()
