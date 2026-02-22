import os
from sqlalchemy.ext.asyncio import create_async_engine

_DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://master:masterpass@localhost:5432/crawler")

# Ensure we always use the asyncpg driver (guard against psycopg2 URLs slipping in)
if _DATABASE_URL.startswith("postgresql://") or _DATABASE_URL.startswith("postgresql+psycopg2://"):
    _DATABASE_URL = _DATABASE_URL.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    _DATABASE_URL = _DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
  url=_DATABASE_URL,
  pool_size=20,
  max_overflow=10,
  pool_pre_ping=True
)