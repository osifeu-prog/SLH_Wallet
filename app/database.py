from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from .config import settings


class Base(DeclarativeBase):
    pass


# Synchronous SQLAlchemy engine (sufficient for our needs)
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    FastAPI dependency that yields a DB session and closes it afterwards.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
