"""Database engine, session factory, and the declarative base for models."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    """Parent class for every table in models.py."""


# pool_pre_ping checks a connection is alive before using it, so a Postgres
# restart doesn't surface as a confusing error on the next request.
engine = create_engine(get_settings().database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
