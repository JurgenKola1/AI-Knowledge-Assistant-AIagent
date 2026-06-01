"""SQLite helpers for document metadata (filename, status, chunk counts)."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from backend.config import DB_PATH


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                stored_path TEXT NOT NULL,
                file_type TEXT NOT NULL,
                page_count INTEGER DEFAULT 0,
                chunk_count INTEGER DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'processing',
                error_message TEXT,
                uploaded_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def create_document(filename: str, stored_path: str, file_type: str) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO documents (filename, stored_path, file_type, status, uploaded_at)
            VALUES (?, ?, ?, 'processing', ?)
            """,
            (filename, stored_path, file_type, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        return int(cursor.lastrowid)


def update_document(
    doc_id: int,
    *,
    status: str,
    page_count: int = 0,
    chunk_count: int = 0,
    error_message: str | None = None,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE documents
            SET status = ?, page_count = ?, chunk_count = ?, error_message = ?
            WHERE id = ?
            """,
            (status, page_count, chunk_count, error_message, doc_id),
        )
        conn.commit()


def list_documents() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, filename, file_type, page_count, chunk_count, status,
                   error_message, uploaded_at
            FROM documents
            ORDER BY uploaded_at DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_document(doc_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM documents WHERE id = ?",
            (doc_id,),
        ).fetchone()
    return dict(row) if row else None


def delete_document_record(doc_id: int) -> dict | None:
    doc = get_document(doc_id)
    if not doc:
        return None
    with get_connection() as conn:
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()
    return doc
