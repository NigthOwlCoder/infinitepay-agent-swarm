import json
import os
import sqlite3
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock


class HistoryService:
    """Append-only conversation history; SQLite locally, replaceable by Postgres."""

    def __init__(self, path: str | None = None) -> None:
        self._fallback: list[dict] = []
        self._lock = Lock()
        configured = path or os.getenv("HISTORY_DB_PATH")
        self.path = (
            Path(configured)
            if configured
            else Path(tempfile.gettempdir()) / "getnet_history.db"
        )
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def record(
        self,
        conversation_id: str,
        actor: str,
        event_type: str,
        content: str,
        metadata: dict | None = None,
    ) -> None:
        created_at = datetime.now(UTC).isoformat()
        serialized = json.dumps(metadata or {}, ensure_ascii=False)
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO history
                        (conversation_id, actor, event_type, content, metadata, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (conversation_id, actor, event_type, content, serialized, created_at),
                )
        except (OSError, sqlite3.Error):
            with self._lock:
                self._fallback.append(
                    {
                        "id": f"memory-{len(self._fallback) + 1}",
                        "conversation_id": conversation_id,
                        "actor": actor,
                        "event_type": event_type,
                        "content": content,
                        "metadata": metadata or {},
                        "created_at": created_at,
                    }
                )

    def list(self, conversation_id: str) -> list[dict]:
        persisted: list[dict] = []
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    "SELECT * FROM history WHERE conversation_id = ? ORDER BY id",
                    (conversation_id,),
                ).fetchall()
            persisted = [
                {**dict(row), "metadata": json.loads(row["metadata"])} for row in rows
            ]
        except (OSError, sqlite3.Error):
            pass
        with self._lock:
            memory = [
                item.copy()
                for item in self._fallback
                if item["conversation_id"] == conversation_id
            ]
        return persisted + memory
