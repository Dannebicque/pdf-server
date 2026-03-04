import os
import time
import json
import shutil
import hashlib
import requests
from pathlib import Path

from .config import settings
from .db import get_conn
from .tmpfiles import ensure_dirs, tmp_pdf_path, sign_tmp_url
from .render_html import render_html
from .render_latex import extract_zip_base64, compile_latex


def post_callback(callback_url: str, body: dict):
    raw = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    sig = __import__("hmac").new(settings.CALLBACK_HMAC_SECRET.encode("utf-8"), raw, __import__("hashlib").sha256).hexdigest()

    r = requests.post(
        callback_url,
        data=raw,
        headers={
            "Authorization": f"Bearer {settings.CALLBACK_BEARER}",
            "Content-Type": "application/json",
            "X-Signature": sig,
        },
        timeout=30,
    )
    r.raise_for_status()


def run_job_from_db(job_id: str):
    ensure_dirs()
    conn = get_conn()
    row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
    conn.close()
    if not row:
        return

    cache_key = row["cache_key"]
    kind = row["kind"]
    callback_url = row["callback_url"]
    options = json.loads(row["options_json"])
    payload = json.loads(row["payload_json"])
    out_tmp_pdf = tmp_pdf_path(job_id)

    workdir = str(Path(settings.WORKDIR_BASE) / job_id)
    Path(workdir).mkdir(parents=True, exist_ok=True)

    logs = None
    error = None

    try:
        filename = options.get("filename") or "document.pdf"
        timeout_seconds = int(options.get("timeoutSeconds") or 300)

        if kind == "html":
            html = payload.get("html")
            if not isinstance(html, str) or not html:
                raise ValueError("payload.html is required")
            render_html(html, out_tmp_pdf, options)
            logs = "HTML rendered via Playwright"

        elif kind == "latex":
            zip_b64 = payload.get("zipBase64")
            if not isinstance(zip_b64, str) or not zip_b64:
                raise ValueError("payload.zipBase64 is required")

            entrypoint = payload.get("entrypoint") or options.get("entrypoint") or "main.tex"
            engine = payload.get("engine") or options.get("engine") or "pdflatex"

            extract_zip_base64(zip_b64, workdir, settings.MAX_LATEX_ZIP_BYTES)
            pdf_path, logs = compile_latex(workdir, entrypoint, engine, timeout_seconds)

            if not os.path.isfile(pdf_path):
                raise RuntimeError("LaTeX compilation did not produce a PDF")

            shutil.copyfile(pdf_path, out_tmp_pdf)

        else:
            raise ValueError("Unknown job type")

        expires = int(time.time()) + int(settings.TMP_URL_TTL_SECONDS)
        sig = sign_tmp_url(job_id, expires)
        temp_url = f"{settings.PUBLIC_SCHEME}://{settings.PUBLIC_HOST}/tmp/{job_id}.pdf?expires={expires}&sig={sig}"

        post_callback(callback_url, {
            "jobId": job_id,
            "cacheKey": cache_key,
            "status": "success",
            "filename": filename,
            "tempPdfUrl": temp_url,
            "logs": logs,
        })

        conn = get_conn()
        conn.execute(
            "UPDATE jobs SET status='success', finished_at=?, logs=? WHERE job_id=?",
            (int(time.time()), logs, job_id),
        )
        conn.close()

    except Exception as e:
        error = str(e)
        try:
            post_callback(callback_url, {
                "jobId": job_id,
                "cacheKey": cache_key,
                "status": "error",
                "errorMessage": error,
                "logs": logs,
            })
        except Exception:
            # callback down, on garde l'erreur en DB
            pass

        conn = get_conn()
        conn.execute(
            "UPDATE jobs SET status='error', finished_at=?, error_message=?, logs=? WHERE job_id=?",
            (int(time.time()), error, logs, job_id),
        )
        conn.close()
    finally:
        shutil.rmtree(workdir, ignore_errors=True)