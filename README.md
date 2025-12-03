# Distributed Web Crawler

A scalable, distributed web crawler built with Python, utilizing a microservices architecture. The system is designed to handle large-scale crawling tasks by distributing work across multiple worker nodes, managed by a central orchestrator.

## 🏗 Architecture

The project consists of three main services:

### 1. Frontier Service (`services/frontier`)
**Role:** API Gateway & State Manager
- **Entry Point:** Exposes a FastAPI REST interface for users to submit crawl requests.
- **State Management:** Stores crawl request status and metadata in MongoDB.
- **Queueing:** Pushes new crawl jobs to the `crawl_requests` RabbitMQ queue.
- **gRPC Server:** Runs a gRPC server (port 50051) for internal service communication (e.g., receiving crawled data from slaves).

### 2. Master Service (`services/master`)
**Role:** Orchestrator & Load Balancer
- **Task Distribution:** Consumes messages from the `crawl_requests` queue.
- **Load Balancing:** Monitors worker load and assigns tasks to the least busy `Slave` instance.
- **Auto-Scaling:** (Planned) Automatically spins up new `Slave` containers via Docker API when load exceeds thresholds.

### 3. Slave Service (`services/slave`)
**Role:** Worker Node
- **Execution:** Listens on a unique, worker-specific queue.
- **Crawling:** Performs the actual HTTP requests and parsing.
- **Reporting:** Sends crawled data back to the Frontier service via gRPC.

## 🛠 Tech Stack

- **Language:** Python 3.13+
- **Package Manager:** `uv`
- **Communication:**
  - **Asynchronous:** RabbitMQ (Task Queues)
  - **Synchronous:** gRPC (Inter-service communication)
- **Database:** MongoDB (Metadata & State)
- **Cache:** Redis (Deduplication & Caching)
- **Containerization:** Docker & Docker Compose

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.13+
- `uv` (Universal Python Package Manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd web-crawler
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

3. **Start Infrastructure**
   Start MongoDB, RabbitMQ, and Redis:
   ```bash
   docker-compose up -d
   ```

4. **Run Services**
   You can run services individually for development:

   *Frontier:*
   ```bash
   uv run services/frontier/src/frontier/main.py
   ```

   *Master:*
   ```bash
   uv run services/master/src/master/main.py
   ```

   *Slave:*
   ```bash
   export WORKER_ID=slave-1
   uv run services/slave/src/slave/main.py
   ```

## 📝 API Usage

**Submit a Crawl Request**
```http
POST http://localhost:8000/crawl
Content-Type: application/json

{
  "url": "https://example.com",
  "depth": 2,
  "max_pages": 100
}
```

## ✅ Status & Roadmap

### Current Features
- [x] Basic Service Structure (Frontier, Master, Slave)
- [x] Docker Compose setup for infrastructure
- [x] Frontier API for accepting requests
- [x] RabbitMQ integration for task passing
- [x] gRPC Protobuf definitions

### 🚧 Remaining TODOs & Improvements

#### Master Service
- [ ] **Implement Task Assignment:** Complete logic in `master/main.py` to forward tasks to specific worker queues instead of just consuming them.
- [ ] **Worker Management:** Implement the logic to track active workers and their load in the database.
- [ ] **Auto-scaling:** Implement Docker SDK integration to spawn new slave containers dynamically.

#### Slave Service
- [ ] **Crawl Logic:** Implement the actual web scraping logic (using `httpx` or `playwright`) in `slave/consume.py`.
- [ ] **Integration:** Connect the `send_url` gRPC call to the crawl loop to report results back to Frontier.

#### Frontier Service
- [ ] **Result Processing:** Implement the gRPC `Crawl` handler to save crawled data to MongoDB.
- [ ] **Deduplication:** Implement Redis-based URL deduplication to avoid re-crawling.

#### General
- [ ] **Configuration:** Move hardcoded values (e.g., `localhost:50051`) to environment variables.
- [ ] **Logging:** Implement structured logging across all services.
- [ ] **Testing:** Add unit and integration tests.
