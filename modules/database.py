"""SQLite metadata persistence; binary image data stays on disk."""
from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


def _connect(database: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(database), timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(database: str | Path) -> None:
    Path(database).parent.mkdir(parents=True, exist_ok=True)
    with _connect(database) as connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS scans (
            id TEXT PRIMARY KEY, original_filename TEXT NOT NULL, generated_filename TEXT NOT NULL,
            processed_at TEXT NOT NULL, processing_mode TEXT NOT NULL, ocr_text TEXT NOT NULL DEFAULT '',
            output_path TEXT NOT NULL, original_path TEXT NOT NULL DEFAULT '', page_count INTEGER NOT NULL DEFAULT 1
        )""")


def save_scan(database: str | Path, *, original_filename: str, generated_filename: str, processing_mode: str,
              output_path: str, original_path: str = "", ocr_text: str = "", page_count: int = 1,
              processed_at: str | None = None) -> str:
    scan_id = uuid.uuid4().hex
    timestamp = processed_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
    with _connect(database) as connection:
        connection.execute("INSERT INTO scans (id,original_filename,generated_filename,processed_at,processing_mode,ocr_text,output_path,original_path,page_count) VALUES (?,?,?,?,?,?,?,?,?)",
                           (scan_id, Path(original_filename).name[:255], Path(generated_filename).name[:255], timestamp,
                            processing_mode[:80], ocr_text, str(output_path), str(original_path), max(1, int(page_count))))
    return scan_id


def list_scans(database: str | Path, query: str = "", limit: int = 500) -> list[dict]:
    term = f"%{query.strip()}%"
    with _connect(database) as connection:
        rows = connection.execute("SELECT * FROM scans WHERE (? = '%%' OR original_filename LIKE ? OR ocr_text LIKE ?) ORDER BY processed_at DESC LIMIT ?",
                                  (term, term, term, int(limit))).fetchall()
    return [dict(row) for row in rows]


def get_scan(database: str | Path, scan_id: str) -> dict | None:
    with _connect(database) as connection:
        row = connection.execute("SELECT * FROM scans WHERE id = ?", (scan_id,)).fetchone()
    return dict(row) if row else None


def update_ocr(database: str | Path, scan_id: str, ocr_text: str) -> None:
    with _connect(database) as connection:
        connection.execute("UPDATE scans SET ocr_text = ? WHERE id = ?", (ocr_text, scan_id))


def delete_scan(database: str | Path, scan_id: str) -> dict | None:
    with _connect(database) as connection:
        row = connection.execute("SELECT * FROM scans WHERE id = ?", (scan_id,)).fetchone()
        if row:
            connection.execute("DELETE FROM scans WHERE id = ?", (scan_id,))
    return dict(row) if row else None


def scan_stats(database: str | Path) -> dict[str, int]:
    with _connect(database) as connection:
        row = connection.execute("SELECT COUNT(*) AS scans, COALESCE(SUM(page_count),0) AS pages FROM scans").fetchone()
    return {"scans": int(row["scans"]), "pages": int(row["pages"])}
