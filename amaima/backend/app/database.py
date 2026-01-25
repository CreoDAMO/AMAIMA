from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

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
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
