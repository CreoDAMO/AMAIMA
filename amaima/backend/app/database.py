from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

_engine = None
_SessionLocal = None


def _get_database_url():
    url = os.getenv("DATABASE_URL", "")
    if not url:
        return None
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def get_engine():
    global _engine
    if _engine is None:
        url = _get_database_url()
        if not url:
            logger.warning("DATABASE_URL not set, database features disabled")
            return None
        _engine = create_engine(url)
    return _engine


def get_session_local():
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        if engine is None:
            return None
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal


class DecisionTelemetry(Base):
    __tablename__ = "decision_telemetry"

    decision_id = Column(String, primary_key=True, index=True)
    query_hash = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    user_id_hash = Column(String, nullable=True)
    complexity_level = Column(String)
    model = Column(String)
    execution_mode = Column(String)
    security_level = Column(String, nullable=True)
    latency_estimate_ms = Column(Integer)
    cost_estimate_usd = Column(Float)
    actual_latency_ms = Column(Integer, nullable=True)
    actual_cost_usd = Column(Float, nullable=True)
    confidence = Column(JSON)
    reason_codes = Column(JSON)
    user_feedback = Column(Integer, nullable=True)
    version = Column(String, nullable=True)


def init_db():
    engine = get_engine()
    if engine is None:
        logger.warning("Skipping DB init - no DATABASE_URL")
        return
    Base.metadata.create_all(bind=engine)
    logger.info("SQLAlchemy tables initialized")


def get_db():
    session_local = get_session_local()
    if session_local is None:
        raise RuntimeError("Database not configured")
    db = session_local()
    try:
        yield db
    finally:
        db.close()
