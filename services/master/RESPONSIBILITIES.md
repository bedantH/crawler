# Master Service Responsibilities

## ✅ Core Responsibilities

### 1. **Worker Lifecycle Management**
- **Creating workers** with unique WORKER_IDs
- Spawning new worker containers using Docker SDK
- Destroying workers when no longer needed
- Tracking worker metadata (worker_id, created_at, status)

**Implementation:**
- Use Docker SDK (`docker` Python package)
- Create containers with unique worker IDs (e.g., `slave-1`, `slave-2`)
- Pass `WORKER_ID` as environment variable to worker containers
- Maintain worker registry in database/memory

---

### 2. **Load Balancing**
- **Intelligent task distribution** across workers
- Monitor worker capacity (current task count)
- Select the least busy worker for new tasks
- Prevent overloading any single worker

**Implementation:**
```python
# Query all workers and their current task counts
# Find worker with minimum task count
# If all workers at MAX_TASKS_THRESHOLD, create new worker
# Push task to selected worker's queue
```

**Queue Pattern:**
```
Master consumes from: crawl_requests
Master pushes to:     worker-{id}-tasks  # e.g., worker-1-tasks, worker-2-tasks
```

---

### 3. **Worker Health-Check**
- **Monitor worker health** via heartbeats
- Detect dead/unresponsive workers
- Track last heartbeat timestamp
- Update worker status (active/idle/offline/error)

**Implementation:**
- Workers send periodic heartbeats via gRPC
- Master updates `last_heartbeat` timestamp
- Background task checks for missed heartbeats
- Mark workers as "offline" if no heartbeat within threshold

**gRPC Method:**
```protobuf
rpc Heartbeat(HeartbeatRequest) returns (HeartbeatResponse);
```

---

### 4. **Failure Handling & Retry Logic**

#### a. **Worker Failure**
- Detect when worker stops sending heartbeats
- Reassign tasks from dead worker to healthy workers
- Clean up dead worker containers
- Create replacement workers if needed

#### b. **Task Failure**
- Handle task processing failures reported by workers
- Implement retry logic (e.g., retry up to 3 times)
- Move permanently failed tasks to dead-letter queue
- Track failure metrics for monitoring

**Implementation:**
```python
# If worker offline and has pending tasks:
#   1. Query tasks assigned to that worker
#   2. Mark tasks as "failed" or "pending_retry"
#   3. Push tasks back to crawl_requests queue
#   4. Destroy dead worker container

# If task fails on worker:
#   1. Worker reports failure back to Master
#   2. Master checks retry_count
#   3. If retry_count < MAX_RETRIES: requeue task
#   4. Else: move to dead-letter queue
```

---

### 5. **Auto-Scaling**
- Automatically spawn new workers when load increases
- Destroy idle workers when load decreases
- Maintain minimum/maximum worker pool size

**Scaling Rules:**
```python
# Scale UP: All workers at MAX_TASKS_THRESHOLD
if all(worker.task_count >= MAX_TASKS_THRESHOLD for worker in workers):
    create_new_worker()

# Scale DOWN: Multiple workers idle for X minutes
if count_idle_workers() > MIN_WORKERS and idle_duration > SCALE_DOWN_THRESHOLD:
    destroy_idle_worker()
```

---

## 🚫 What Master Does NOT Do

- ❌ **Worker self-registration** (Master creates workers, so it already knows them)
- ❌ **Actual web crawling** (Workers do this)
- ❌ **Storing crawled data** (Frontier handles this)
- ❌ **URL deduplication** (Frontier + Redis)
- ❌ **Metrics collection** (postponed for later)

---

## 🏗️ Architecture Overview

```
┌─────────────┐
│  Frontier   │ (Receives crawl requests)
└──────┬──────┘
       │ Pushes to queue
       ▼
┌──────────────────┐
│ crawl_requests   │ (RabbitMQ Queue)
│     (Queue)      │
└──────┬───────────┘
       │ Master consumes
       ▼
┌──────────────────┐
│     MASTER       │
│                  │
│ - Load balance   │
│ - Create workers │
│ - Health check   │
│ - Failure handle │
└──────┬───────────┘
       │ Pushes to worker queues
       ▼
┌─────────────────────────────────┐
│  worker-1-tasks | worker-2-tasks │ (Per-worker queues)
└────────┬────────────────┬────────┘
         │                │
         ▼                ▼
    ┌─────────┐      ┌─────────┐
    │ Worker 1│      │ Worker 2│
    └─────────┘      └─────────┘
         │                │
         └────────┬───────┘
                  │ Send results via gRPC
                  ▼
            ┌──────────┐
            │ Frontier │ (Stores results)
            └──────────┘
```

---

## 📋 Communication Patterns

### Queue-Based (RabbitMQ)
- **Master consumes:** `crawl_requests` queue
- **Master produces:** `worker-{id}-tasks` queues
- **Workers consume:** Their individual `worker-{id}-tasks` queue

### gRPC-Based
- **Workers → Master:** Heartbeat (health reporting)
- **Workers → Frontier:** Crawled data submission
- **Admin/Monitoring → Master:** Status queries (GetWorkerStatus, ListWorkers)

---

## 🎯 Implementation Priority

1. ✅ **Load balancing logic** (partially done in `main.py`)
2. 🔨 **Task assignment to worker queues** (TODO)
3. 🔨 **Worker creation via Docker SDK** (TODO)
4. 🔨 **Heartbeat gRPC server** (TODO)
5. 🔨 **Failure detection** (TODO)
6. 🔨 **Retry logic** (TODO)
7. 🔨 **Auto-scaling** (TODO)
8. ⏳ **Metrics** (Later)
