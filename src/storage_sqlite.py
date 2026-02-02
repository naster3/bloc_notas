from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Callable, Iterable, TypeVar, Mapping, Any, cast
from uuid import uuid4

from .models import (
    Note,
    join_tags,
    normalize_tags,
    normalize_title,
    title_from_content,
    utc_now_iso,
)


SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT NOT NULL,
    pinned INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_notes_updated_at ON notes(updated_at);
CREATE INDEX IF NOT EXISTS idx_notes_pinned ON notes(pinned);
CREATE INDEX IF NOT EXISTS idx_notes_title ON notes(title);
CREATE INDEX IF NOT EXISTS idx_notes_content ON notes(content);
"""


class NoteStoreError(RuntimeError):
    pass


T = TypeVar("T")


class NoteStore:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._ensure_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _execute(self, operation: Callable[[sqlite3.Connection], T]) -> T:
        try:
            with self._connect() as conn:
                return operation(conn)
        except sqlite3.Error as exc:
            raise NoteStoreError(str(exc)) from exc

    def _ensure_db(self) -> None:
        self._execute(lambda conn: conn.executescript(SCHEMA))

    def _row_to_note(self, row: sqlite3.Row) -> Note:
        return Note.from_row(cast(Mapping[str, Any], row))

    def list_notes(
        self,
        query: str | None = None,
        *,
        tags: Iterable[str] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Note]:
        query_text = (query or "").strip().lower()
        tags_list = [tag.lower() for tag in normalize_tags(tags or [])]

        def op(conn: sqlite3.Connection) -> list[Note]:
            conditions: list[str] = []
            params: list[object] = []
            if query_text:
                like = f"%{query_text}%"
                conditions.append("(lower(title) LIKE ? OR lower(content) LIKE ?)")
                params.extend([like, like])
            for tag in tags_list:
                conditions.append("(',' || lower(tags) || ',') LIKE ?")
                params.append(f"%,{tag},%")
            sql = "SELECT * FROM notes"
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            sql += " ORDER BY pinned DESC, updated_at DESC"
            if limit is not None:
                sql += " LIMIT ?"
                params.append(int(limit))
            if offset is not None:
                sql += " OFFSET ?"
                params.append(int(offset))
            rows = conn.execute(sql, params).fetchall()
            return [self._row_to_note(row) for row in rows]

        return self._execute(op)

    def get_note(self, note_id: str) -> Note | None:
        def op(conn: sqlite3.Connection) -> Note | None:
            row = conn.execute(
                "SELECT * FROM notes WHERE id = ?",
                (note_id,),
            ).fetchone()
            if not row:
                return None
            return self._row_to_note(row)

        return self._execute(op)

    def create_note(
        self,
        title: str,
        content: str,
        tags: Iterable[str] | None = None,
        pinned: bool = False,
    ) -> Note:
        now = utc_now_iso()
        note_id = str(uuid4())
        normalized_title = normalize_title(title)
        normalized_tags = normalize_tags(tags or [])
        tag_text = join_tags(normalized_tags)

        def op(conn: sqlite3.Connection) -> Note:
            conn.execute(
                """
                INSERT INTO notes (id, title, content, tags, pinned, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (note_id, normalized_title, content, tag_text, int(pinned), now, now),
            )
            return Note(
                id=note_id,
                title=normalized_title,
                content=content,
                tags=normalized_tags,
                pinned=bool(pinned),
                created_at=now,
                updated_at=now,
            )

        return self._execute(op)

    def update_note(
        self,
        note_id: str,
        title: str,
        content: str,
        tags: Iterable[str] | None = None,
        pinned: bool = False,
    ) -> Note | None:
        now = utc_now_iso()
        normalized_title = normalize_title(title)
        normalized_tags = normalize_tags(tags or [])
        tag_text = join_tags(normalized_tags)

        def op(conn: sqlite3.Connection) -> Note | None:
            conn.execute(
                """
                UPDATE notes
                SET title = ?, content = ?, tags = ?, pinned = ?, updated_at = ?
                WHERE id = ?
                """,
                (normalized_title, content, tag_text, int(pinned), now, note_id),
            )
            row = conn.execute(
                "SELECT * FROM notes WHERE id = ?",
                (note_id,),
            ).fetchone()
            if not row:
                return None
            return self._row_to_note(row)

        return self._execute(op)

    def delete_note(self, note_id: str) -> bool:
        def op(conn: sqlite3.Connection) -> bool:
            cur = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            return cur.rowcount > 0

        return self._execute(op)

    def upsert_from_content(
        self, note_id: str | None, content: str, tags: Iterable[str] | None = None
    ) -> Note | None:
        title = title_from_content(content)
        if note_id is None:
            if not content.strip():
                return None
            return self.create_note(title=title, content=content, tags=tags or [])
        return self.update_note(note_id, title=title, content=content, tags=tags or [])

    def create_notes(
        self,
        notes: Iterable[tuple[str, str, Iterable[str] | None, bool]],
    ) -> list[Note]:
        items = list(notes)
        if not items:
            return []

        def op(conn: sqlite3.Connection) -> list[Note]:
            created: list[Note] = []
            for title, content, tags, pinned in items:
                now = utc_now_iso()
                note_id = str(uuid4())
                normalized_title = normalize_title(title)
                normalized_tags = normalize_tags(tags or [])
                tag_text = join_tags(normalized_tags)
                conn.execute(
                    """
                    INSERT INTO notes (id, title, content, tags, pinned, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        note_id,
                        normalized_title,
                        content,
                        tag_text,
                        int(pinned),
                        now,
                        now,
                    ),
                )
                created.append(
                    Note(
                        id=note_id,
                        title=normalized_title,
                        content=content,
                        tags=normalized_tags,
                        pinned=bool(pinned),
                        created_at=now,
                        updated_at=now,
                    )
                )
            return created

        return self._execute(op)

    def upsert_many(
        self,
        items: Iterable[tuple[str | None, str, Iterable[str] | None, bool]],
    ) -> list[Note | None]:
        entries = list(items)
        if not entries:
            return []

        def op(conn: sqlite3.Connection) -> list[Note | None]:
            results: list[Note | None] = []
            for note_id, content, tags, pinned in entries:
                title = title_from_content(content)
                normalized_tags = normalize_tags(tags or [])
                tag_text = join_tags(normalized_tags)
                now = utc_now_iso()
                if note_id is None:
                    if not content.strip():
                        results.append(None)
                        continue
                    new_id = str(uuid4())
                    conn.execute(
                        """
                        INSERT INTO notes (id, title, content, tags, pinned, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (new_id, title, content, tag_text, int(pinned), now, now),
                    )
                    results.append(
                        Note(
                            id=new_id,
                            title=title,
                            content=content,
                            tags=normalized_tags,
                            pinned=bool(pinned),
                            created_at=now,
                            updated_at=now,
                        )
                    )
                    continue
                conn.execute(
                    """
                    UPDATE notes
                    SET title = ?, content = ?, tags = ?, pinned = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (title, content, tag_text, int(pinned), now, note_id),
                )
                row = conn.execute(
                    "SELECT * FROM notes WHERE id = ?",
                    (note_id,),
                ).fetchone()
                if not row:
                    results.append(None)
                else:
                    results.append(self._row_to_note(row))
            return results

        return self._execute(op)

    def clear_all(self) -> int:
        def op(conn: sqlite3.Connection) -> int:
            cur = conn.execute("DELETE FROM notes")
            return cur.rowcount

        return self._execute(op)
