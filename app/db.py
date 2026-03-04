import sqlite3
from pathlib import Path
from .config import settings


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.DB_PATH, timeout=30, isolation_level=None)  # autocommit mode
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    Path(settings.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = get_conn()
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            cache_key TEXT NOT NULL,
            kind TEXT NOT NULL, -- html|latex
            callback_url TEXT NOT NULL,
            options_json TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            status TEXT NOT NULL, -- queued|running|success|error
            created_at INTEGER NOT NULL,
            started_at INTEGER,
            finished_at INTEGER,
            error_message TEXT,
            logs TEXT
        );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status_created ON jobs(status, created_at);")
    finally:
        conn.close()