"""Database connection: engine, session factory, Base class and the get_db dependency."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Every model in app/models inherits from this."""


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
