from __future__ import annotations

from pathlib import Path
import sqlite3

from app.core.backup import create_backup, restore_backup


def _read_value(db_path: Path) -> str:
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT name FROM sample WHERE id = 1").fetchone()
    return row[0]


def test_backup_restore_roundtrip(tmp_path: Path) -> None:
    db_path = tmp_path / "app.db"
    backup_dir = tmp_path / "backups"

    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
        conn.execute("INSERT INTO sample (name) VALUES (?)", ("valor-original",))
        conn.commit()

    backup_file = create_backup(backup_dir, database_url=f"sqlite:///{db_path}")

    with sqlite3.connect(db_path) as conn:
        conn.execute("UPDATE sample SET name = ? WHERE id = 1", ("valor-alterado",))
        conn.commit()

    assert _read_value(db_path) == "valor-alterado"

    restore_backup(backup_file, database_url=f"sqlite:///{db_path}")

    assert _read_value(db_path) == "valor-original"
