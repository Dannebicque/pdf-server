import time
from pathlib import Path
from app.config import settings

def purge_tmp(older_than_seconds: int = 3600):
    now = time.time()
    tmp_dir = Path(settings.TMP_PDF_DIR)
    if not tmp_dir.exists():
        return

    for p in tmp_dir.glob("*.pdf"):
        try:
            if (now - p.stat().st_mtime) > older_than_seconds:
                p.unlink(missing_ok=True)
        except Exception:
            pass

if __name__ == "__main__":
    purge_tmp(older_than_seconds=3600)