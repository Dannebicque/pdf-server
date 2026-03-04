import hmac
import hashlib
from fastapi import Header, HTTPException, Request
from .config import settings


def hmac_sha256(secret: str, raw: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()


async def verify_api_auth(request: Request, authorization: str | None = Header(default=None), x_signature: str | None = Header(default=None)):
    if authorization != f"Bearer {settings.PDF_API_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    raw = await request.body()
    if len(raw) > settings.MAX_PAYLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Payload too large")

    if not x_signature:
        raise HTTPException(status_code=400, detail="Missing X-Signature")

    expected = hmac_sha256(settings.PDF_API_HMAC_SECRET, raw)
    if not hmac.compare_digest(expected, x_signature):
        raise HTTPException(status_code=400, detail="Bad signature")