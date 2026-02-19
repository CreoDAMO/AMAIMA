import os
import logging

logger = logging.getLogger(__name__)

_DB_URL_KEYS = [
    "DATABASE_URL",
    "POSTGRES_URL",
    "SUPABASE_DB_URL",
    "POSTGRES_CONNECTION_STRING",
    "PG_CONNECTION_STRING",
]

_RENDER_SECRETS_DIR = "/etc/secrets"


def _read_secret_file(name: str) -> str | None:
    for secrets_dir in [_RENDER_SECRETS_DIR, "/app/etc/secrets"]:
        path = os.path.join(secrets_dir, name)
        if os.path.isfile(path):
            try:
                with open(path, "r") as f:
                    val = f.read().strip()
                if val:
                    return val
            except Exception:
                pass
    return None


def get_database_url() -> str | None:
    for key in _DB_URL_KEYS:
        url = os.getenv(key)
        if url:
            logger.info("Database URL found via env var %s", key)
            return url
    for key in _DB_URL_KEYS:
        url = _read_secret_file(key)
        if url:
            logger.info("Database URL found via secret file %s", key)
            return url
    return None


def get_database_url_for_sqlalchemy() -> str | None:
    url = get_database_url()
    if not url:
        return None
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url
