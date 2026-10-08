"""SQLite database storage and initialization for Flash Automator."""
from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Optional

from ..utils.config import get_config
from ..utils.logger import get_logger

logger = get_logger("database")

_local = threading.local()


class Database:
    """Thread-safe SQLite manager for project and audit persistence."""

    def __init__(self, db_path: Optional[str | Path] = None) -> None:
        if db_path is None:
            self.db_path = get_config().db_file_path
        else:
            self.db_path = Path(db_path)

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def get_connection(self) -> sqlite3.Connection:
        """Get a thread-local SQLite connection for this specific db_path."""
        if not hasattr(_local, "connections"):
            _local.connections = {}
        path_str = str(self.db_path.resolve())
        if path_str not in _local.connections:
            conn = sqlite3.connect(path_str, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA journal_mode = WAL;")
            _local.connections[path_str] = conn
        return _local.connections[path_str]

    def _init_schema(self) -> None:
        """Create necessary database tables if they do not exist."""
        conn = self.get_connection()
        with conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS workflows (
                    id TEXT PRIMARY KEY,
                    project_id TEXT,
                    name TEXT NOT NULL,
                    description TEXT,
                    actions_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS execution_logs (
                    id TEXT PRIMARY KEY,
                    project_id TEXT,
                    workflow_id TEXT,
                    iteration INTEGER NOT NULL,
                    date_value TEXT,
                    status TEXT NOT NULL,
                    details TEXT,
                    output_file TEXT,
                    duration_sec REAL DEFAULT 0.0,
                    created_at REAL NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_workflows_proj ON workflows(project_id);
                CREATE INDEX IF NOT EXISTS idx_logs_wf ON execution_logs(workflow_id);
                CREATE INDEX IF NOT EXISTS idx_logs_created ON execution_logs(created_at);
                """
            )
        logger.info(f"Database schema initialized at {self.db_path}")


_global_db: Optional[Database] = None


def get_db(db_path: Optional[str | Path] = None) -> Database:
    """Retrieve or initialize the singleton database manager."""
    global _global_db
    if _global_db is None or (db_path and str(db_path) != str(_global_db.db_path)):
        _global_db = Database(db_path)
    return _global_db
