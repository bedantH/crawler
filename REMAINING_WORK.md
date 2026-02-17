# Remaining Work — Basic Crawling Flow & DB Storage

## Current State ✅ (What's Done)

| Component | Status |
|-----------|--------|
| **Frontier** — REST API (`POST /crawl`) | ✅ Accepts crawl requests, saves to `CrawlRequest` table, publishes to RabbitMQ |
| **Frontier** — gRPC server | ✅ Skeleton exists (`CrawlServicer`), but just prints and returns `"queued"` |
| **Master** — RabbitMQ consumer | ✅ Consumes from `crawl_requests_queue` |
| **Master** — Task Dispatcher | ✅ Load-balancing logic, creates `Task` in DB, assigns to least-busy worker |
| **Master** — Worker Manager | ✅ `create_worker`, `assign_task_to_worker`, `kill_worker` implemented |
| **Slave** — Queue consumer | ✅ Reads from per-worker queue, creates `Task` dataclass, puts on fetch queue |
| **Slave** — Fetcher | ✅ Fetches raw HTML via `aiohttp` |
| **Slave** — Parser | ✅ Extracts title, headings, links, meta, body text using BeautifulSoup |
| **Slave** — DB Write (Document) | ✅ Creates `Document` record in Postgres with parsed data |
| **DB Models** | ✅ `CrawlRequest`, `Task`, `Worker`, `Document` models exist |

---

## What's Remaining 🚧

### 1. Frontier — gRPC `CrawlRequest` handler is a no-op
The `CrawlServicer.CrawlRequest()` just prints and returns `"queued"`. It needs to:
- Actually receive crawled links from Workers
- Deduplicate URLs (check if already crawled/queued)
- Create new `CrawlRequest` records or queue new tasks for discovered links

### 2. URL Deduplication (Redis)
There's **no Redis integration** anywhere. The README mentions Redis for deduplication, but it's not implemented. Before re-crawling a discovered link, the system needs to check if it was already visited/queued.

### 3. Depth tracking is broken
- Frontier's `POST /crawl` always publishes `"depth": 0` regardless of the user-specified depth
- The parser's `extract_links` doesn't pass a `base_url` (hardcoded as `""`) — relative URLs won't resolve correctly
- There's no depth decrement logic: when discovered links are re-queued, depth should decrease by 1 and stop at 0

### 4. `FrontierClient.send_crawl_request()` sends a list of URLs, but the protobuf field is `url` (singular)
The parser calls `frontier_client.send_crawl_request(url=extracted_data.links, ...)` passing a **list**, but the `FrontierRequest` proto likely has `url` as a single string. This would fail at runtime. Each link needs to be sent individually, or the proto needs a `repeated` field.

### 5. Indexer is a stub
`indexer_worker()` does nothing real — it just simulates 0.2s of work. It's also **never called** since the parser doesn't forward tasks to the indexer queue (`worker.send_to_indexer()` is never invoked after parsing).

### 6. No `crawl_request_id` linkage on `Document`
The `Document` model has no foreign key back to `CrawlRequest`. There's no way to know which crawl job a document belongs to, so you can't query "give me all pages found for crawl request X."

### 7. No `CrawlRequest` status updates
The `CrawlRequest` status is set to `PENDING` on creation but **never updated** to `IN_PROGRESS` or `COMPLETED`. There's no mechanism to mark a crawl job as finished.

### 8. Task status not updated by Worker
The `Task` model has `status`, `started_at`, `finished_at`, and `error` fields, but the Worker **never reports back** to the Master after completing/failing a task. The Master's gRPC `ReportTaskUpdate` handler isn't wired to the worker flow.

### 9. Database URL is hardcoded
`engine.py` has `DATABASE_URL` hardcoded as `postgresql://master:masterpass@localhost:5432/crawler`. Should come from environment variables, especially for Docker.

### 10. No database migration / table creation
There's a `setup_db.py` in shared, but it's unclear if tables are auto-created. Without an Alembic migration or startup `create_all`, the app may crash on first run.

---

## Priority for a Working Basic Flow

If you just want **"submit URL → crawl → store results in DB"** end-to-end, here's the minimal list:

| # | Item | Where |
|---|------|-------|
| 1 | **Fix `base_url` in `extract_links`** — pass the seed URL so relative links resolve | `parser.py` |
| 2 | **Fix depth propagation** — Frontier should pass actual depth, parser should decrement before re-queuing | `frontier/main.py`, `parser.py` |
| 3 | **Fix or remove `FrontierClient.send_crawl_request`** — either loop over links individually or make proto `repeated` | `crawl_request.py` + proto |
| 4 | **Implement Frontier gRPC handler** to actually queue discovered links | `frontier_grpc_server.py` |
| 5 | **Add URL deduplication** — even a simple Postgres `SELECT` on the `Document.url` unique constraint, or a Redis set | `frontier_grpc_server.py` or `parser.py` |
| 6 | **Link `Document` to `CrawlRequest`** with a FK so you can retrieve results per crawl job | `document.py` model |
| 7 | **Update `CrawlRequest` status** to `COMPLETED` when depth is exhausted | Frontier or Master |
| 8 | **Ensure tables are created on startup** (`SQLModel.metadata.create_all`) | `setup_db.py` / service `main.py` |

> Items 1–5 are **blockers** for even a single multi-page crawl to work correctly.
> Items 6–8 are needed to actually retrieve and track results.
