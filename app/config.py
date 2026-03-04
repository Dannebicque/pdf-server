from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PDF_SERVER_HOST: str = "0.0.0.0"
    PDF_SERVER_PORT: int = 8088

    PDF_API_TOKEN: str
    PDF_API_HMAC_SECRET: str

    TMP_URL_HMAC_SECRET: str
    TMP_URL_TTL_SECONDS: int = 900

    WORKDIR_BASE: str = "./var/lib/pdf-server/work"
    TMP_PDF_DIR: str = "./var/lib/pdf-server/tmp"

    DB_PATH: str = "./var/lib/pdf-server/pdf-server.sqlite"

    CALLBACK_BEARER: str
    CALLBACK_HMAC_SECRET: str

    MAX_PAYLOAD_BYTES: int = 15_000_000
    MAX_LATEX_ZIP_BYTES: int = 25_000_000

    PUBLIC_HOST: str = "pdf.example.org"
    PUBLIC_SCHEME: str = "https"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()