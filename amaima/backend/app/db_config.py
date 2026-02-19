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


def get_database_url() -> str | None:
    for key in _DB_URL_KEYS:
        url = os.getenv(key)
        if url:
            logger.info("Database URL found via %s", key)
            return url
    return None


def get_database_url_for_sqlalchemy() -> str | None:
    url = get_database_url()
    if not url:
        return None
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url
