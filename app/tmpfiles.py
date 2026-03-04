import os
import time
import hmac
import hashlib
from pathlib import Path
from fastapi import HTTPException
from .config import settings


def ensure_dirs():
    Path(settings.WORKDIR_BASE).mkdir(parents=True, exist_ok=True)
    Path(settings.TMP_PDF_DIR).mkdir(parents=True, exist_ok=True)


def tmp_pdf_path(job_id: str) -> str:
    return str(Path(settings.TMP_PDF_DIR) / f"{job_id}.pdf")


def sign_tmp_url(job_id: str, expires: int) -> str:
    msg = f"{job_id}|{expires}".encode("utf-8")
    return hmac.new(settings.TMP_URL_HMAC_SECRET.encode("utf-8"), msg, hashlib.sha256).hexdigest()


def verify_tmp_url(job_id: str, expires: int, sig: str):
    now = int(time.time())
    if now > expires:
        raise HTTPException(status_code=410, detail="Expired")
    expected = sign_tmp_url(job_id, expires)
    if not hmac.compare_digest(expected, sig):
        raise HTTPException(status_code=403, detail="Forbidden")