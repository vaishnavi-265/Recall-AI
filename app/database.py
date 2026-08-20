import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime

from .models import Memory

DB_PATH = os.getenv("RECALL_AI_DB", "recall_ai.db")


@contextmanager
def connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL,
                content TEXT NOT NULL,
                project TEXT NOT NULL,
                provider TEXT NOT NULL,
                source_conversation_id TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_project ON memories(project)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_kind ON memories(kind)")


def insert_memory(memory: Memory) -> Memory:
    with connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO memories
            (kind, content, project, provider, source_conversation_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                memory.kind,
                memory.content,
                memory.project,
                memory.provider,
                memory.source_conversation_id,
                memory.created_at.isoformat(),
            ),
        )
        return memory.model_copy(update={"id": cursor.lastrowid})


def _row_to_memory(row: sqlite3.Row) -> Memory:
    return Memory(
        id=row["id"],
        kind=row["kind"],
        content=row["content"],
        project=row["project"],
        provider=row["provider"],
        source_conversation_id=row["source_conversation_id"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def search_memories(query: str, limit: int = 20) -> list[Memory]:
    terms = [term.lower() for term in query.split() if term.strip()]
    if not terms:
        return []

    with connection() as conn:
        rows = conn.execute("SELECT * FROM memories ORDER BY created_at DESC").fetchall()

    scored: list[tuple[int, Memory]] = []
    for row in rows:
        memory = _row_to_memory(row)
        haystack = f"{memory.content} {memory.project} {memory.kind} {memory.provider}".lower()
        score = sum(haystack.count(term) for term in terms)
        if score:
            scored.append((score, memory))

    scored.sort(key=lambda item: (item[0], item[1].created_at), reverse=True)
    return [memory for _, memory in scored[:limit]]


def project_timeline(project: str) -> list[Memory]:
    with connection() as conn:
        rows = conn.execute(
            "SELECT * FROM memories WHERE lower(project) = lower(?) ORDER BY created_at ASC, id ASC",
            (project,),
        ).fetchall()
    return [_row_to_memory(row) for row in rows]


def open_tasks() -> list[Memory]:
    with connection() as conn:
        rows = conn.execute(
            "SELECT * FROM memories WHERE kind = 'task' ORDER BY created_at DESC, id DESC"
        ).fetchall()
    return [_row_to_memory(row) for row in rows]
