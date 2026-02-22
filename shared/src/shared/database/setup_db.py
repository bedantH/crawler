from sqlmodel import SQLModel
from shared.database.engine import engine
from shared.database.models import crawl_requests, task, worker, document  # noqa: F401 - import models so metadata is populated

async def create_db_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)