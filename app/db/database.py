from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import DATABASE_URL

# Synchronous engine using psycopg2-compatible URL (e.g. postgresql://user:pwd@host:port/dbname)
engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
    expire_on_commit=False,
)


def get_db():
    """Dependency for FastAPI that yields a synchronous SQLAlchemy Session.

    Note: Using sync DB sessions inside async endpoints will run in the threadpool
    and may block if used heavily. Prefer async engine (`AsyncSession`) for high
    throughput async apps. This change only updates the DB helper to use a
    synchronous engine because your DATABASE_URL is psycopg2-based.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
