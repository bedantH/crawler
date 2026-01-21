from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = "postgresql://master:masterpass@localhost:5432/crawler"

engine = create_async_engine(
  url=DATABASE_URL,
  pool_size=20,
  max_overflow=10,
  pool_pre_ping=True
)