"""
Database Configuration — Serverless-Safe SQLAlchemy.

SEV-1 FIX (Connection Pool Exhaustion):
  Cloud Run scales to N instances. Each instance with QueuePool(pool_size=10, max_overflow=20)
  means 50 instances × 30 = 1,500 connections, obliterating pg_max_connections (default 100).
  SOLUTION: NullPool for Cloud Run — each request gets its own connection and releases it
  immediately. For local/dev, use a conservative QueuePool.

  Also exports SQLALCHEMY_DATABASE_URL for Alembic's env.py.
"""
import os
from sqlalchemy import create_engine  # type: ignore
from sqlalchemy.orm import sessionmaker, declarative_base  # type: ignore
from sqlalchemy.pool import NullPool, QueuePool  # type: ignore

from app.config import settings  # type: ignore

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Detect Cloud Run environment
IS_CLOUD_RUN = os.getenv("K_SERVICE") is not None

if IS_CLOUD_RUN:
    # NullPool: no persistent connections — safe for serverless scaling.
    # Cloud SQL Auth Proxy manages the actual connection efficiency.
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        poolclass=NullPool,
        echo=False,
    )
else:
    # Local/dev: a small bounded pool to prevent connection storms during testing.
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=1800,
        echo=False,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a scoped DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
