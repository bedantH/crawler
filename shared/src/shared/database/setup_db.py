from sqlmodel import SQLModel
from shared.database.engine import engine
from shared.database.models import crawl_requests, task, worker

SQLModel.metadata.create_all(engine)
print("Tables Created")