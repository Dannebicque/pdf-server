from pydantic import BaseModel, Field
from typing import Literal, Any


JobKind = Literal["html", "latex"]


class JobOptions(BaseModel):
    filename: str = "document.pdf"
    timeoutSeconds: int = 300

    # html options
    pageFormat: str | None = None  # e.g. "A4"
    marginTop: str | None = None
    marginRight: str | None = None
    marginBottom: str | None = None
    marginLeft: str | None = None

    # latex options
    entrypoint: str | None = None  # "main.tex"
    engine: str | None = None      # "pdflatex" / "lualatex" / "xelatex"


class CreateJobRequest(BaseModel):
    type: JobKind
    jobId: str
    cacheKey: str
    callbackUrl: str
    options: JobOptions = Field(default_factory=JobOptions)
    payload: dict[str, Any]


class CallbackBody(BaseModel):
    jobId: str
    cacheKey: str
    status: Literal["success", "error"]
    filename: str | None = None
    tempPdfUrl: str | None = None
    logs: str | None = None
    errorMessage: str | None = None