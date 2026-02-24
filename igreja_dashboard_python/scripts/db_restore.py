from __future__ import annotations

import argparse
from pathlib import Path

from app.core.backup import restore_backup


def main() -> None:
    parser = argparse.ArgumentParser(description="Restaura backup SQLite da aplicação.")
    parser.add_argument("backup_file", help="Arquivo de backup a ser restaurado.")
    args = parser.parse_args()

    target = restore_backup(Path(args.backup_file))
    print(target)


if __name__ == "__main__":
    main()
