from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import json
import time

from .models import CreateJobRequest
from .security import verify_api_auth
from .tmpfiles import ensure_dirs, tmp_pdf_path, verify_tmp_url
from .db import init_db, get_conn

app = FastAPI(title="PDF Server (SQLite queue)")

ensure_dirs()
init_db()

@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Not found")
        return {
            "jobId": row["job_id"],
            "status": row["status"],
            "kind": row["kind"],
            "errorMessage": row["error_message"],
            "logs": row["logs"],
        }
    finally:
        conn.close()

@app.post("/api/jobs")
def create_job(req: CreateJobRequest, _=Depends(verify_api_auth)):
    now = int(time.time())
    conn = get_conn()
    try:
        # idempotent : si le job_id existe déjà, on ne recrée pas
        row = conn.execute("SELECT job_id, status FROM jobs WHERE job_id = ?", (req.jobId,)).fetchone()
        if row:
            return {"status": row["status"], "jobId": req.jobId}

        conn.execute(
            """INSERT INTO jobs(job_id, cache_key, kind, callback_url, options_json, payload_json, status, created_at)
               VALUES(?,?,?,?,?,?,?,?)""",
            (
                req.jobId,
                req.cacheKey,
                req.type,
                req.callbackUrl,
                json.dumps(req.options.model_dump(), ensure_ascii=False, separators=(",", ":")),
                json.dumps(req.payload, ensure_ascii=False, separators=(",", ":")),
                "queued",
                now,
            ),
        )
        return {"status": "queued", "jobId": req.jobId}
    finally:
        conn.close()


@app.get("/tmp/{job_id}.pdf")
def get_tmp_pdf(job_id: str, expires: int, sig: str):
    verify_tmp_url(job_id, expires, sig)
    path = tmp_pdf_path(job_id)
    if not Path(path).is_file():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(path, media_type="application/pdf", filename=f"{job_id}.pdf")

@app.post("/_test/callback")
def test_callback(payload: dict):
    # juste pour tests
    return {"ok": True}