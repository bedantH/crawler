import sqlite3
from services.frontier.src.frontier.utils.logger import logger

conn = sqlite3.connect("workers.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

def init():
  # create an initial tables
  create_workers_table_query = """
    CREATE TABLE IF NOT EXISTS workers (
      id TEXT PRIMARY KEY,
      hostname TEXT,
      status TEXT,
      last_heartbeat DATETIME,
      registered_at DATETIME,
      total_tasks_completed INTEGER DEFAULT 0,
      avg_task_duration REAL,
    )
  """

  create_tasks_table_query = """
    CREATE TABLE IF NOT EXISTS tasks (
      id TEXT PRIMARY KEY,
      worker_id TEXT,
      status TEXT,
      payload TEXT,
      created_at DATETIME,
      started_at DATETIME,
      finished_at DATETIME,
      retries INTEGER DEFAULT 0,
      FOREIGN KEY(worker_id) REFERENCES workers(id)
    );
  """

  cursor.execute(create_tasks_table_query)
  cursor.execute(create_workers_table_query)