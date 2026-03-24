"""
Database Configuration — Production-grade SQLAlchemy with connection pooling.

Strict Mandates:
  • Connection pooling with pool_pre_ping for stale connection detection
  • pool_recycle to prevent long-lived connections from being killed by Postgres
"""
from sqlalchemy import create_engine  # type: ignore
from sqlalchemy.orm import sessionmaker, declarative_base  # type: ignore

from app.config import settings  # type: ignore

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
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
