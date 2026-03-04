import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import json
import time
import sqlite3

from app.db import get_conn, init_db
from app.tasks import run_job_from_db


POLL_SECONDS = 1


def claim_next_job(conn: sqlite3.Connection):
    """
    Claim atomiquement 1 job queued.
    SQLite n'a pas SKIP LOCKED, donc on fait une transaction IMMEDIATE
    pour éviter les doubles claims.
    """
    conn.execute("BEGIN IMMEDIATE;")
    row = conn.execute(
        "SELECT job_id FROM jobs WHERE status='queued' ORDER BY created_at ASC LIMIT 1"
    ).fetchone()

    if not row:
        conn.execute("COMMIT;")
        return None

    job_id = row["job_id"]
    now = int(time.time())

    conn.execute(
        "UPDATE jobs SET status='running', started_at=? WHERE job_id=? AND status='queued'",
        (now, job_id),
    )
    conn.execute("COMMIT;")
    return job_id


def main():
    init_db()
    while True:
        conn = get_conn()
        try:
            job_id = claim_next_job(conn)
        except Exception:
            try:
                conn.execute("ROLLBACK;")
            except Exception:
                pass
            conn.close()
            time.sleep(POLL_SECONDS)
            continue
        finally:
            conn.close()

        if not job_id:
            time.sleep(POLL_SECONDS)
            continue

        run_job_from_db(job_id)


if __name__ == "__main__":
    main()