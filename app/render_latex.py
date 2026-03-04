import base64
import os
import shutil
import subprocess
import zipfile
from pathlib import Path


def extract_zip_base64(zip_b64: str, target_dir: str, max_bytes: int):
    raw = base64.b64decode(zip_b64, validate=True)
    if len(raw) > max_bytes:
        raise ValueError("zip too large")

    zpath = Path(target_dir) / "src.zip"
    zpath.write_bytes(raw)

    with zipfile.ZipFile(zpath, "r") as z:
        z.extractall(target_dir)

    zpath.unlink(missing_ok=True)


def compile_latex(workdir: str, entrypoint: str, engine: str | None, timeout_seconds: int) -> tuple[str, str]:
    # latexmk multi-pass
    # sécurité : pas de shell-escape
    # engine option: -pdf (pdflatex) / -lualatex / -xelatex
    cmd = ["latexmk", "-interaction=nonstopmode", "-halt-on-error", "-no-shell-escape"]

    if engine == "lualatex":
        cmd += ["-lualatex"]
    elif engine == "xelatex":
        cmd += ["-xelatex"]
    else:
        cmd += ["-pdf"]

    cmd += [entrypoint]

    p = subprocess.run(
        cmd,
        cwd=workdir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout_seconds,
        check=False,
        text=True,
    )
    log = p.stdout[-200000:]  # limiter la taille
    pdf_path = str(Path(workdir) / Path(entrypoint).with_suffix(".pdf").name)
    return pdf_path, log