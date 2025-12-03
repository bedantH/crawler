# Web Crawler Architecture - Master & Worker Design

## ✅ Architecture Overview

This document defines the complete architecture for the Master-Worker distributed web crawler system.

---

## 🎯 Master Responsibilities

### 1. **Worker Lifecycle Management**
- Create workers with unique `WORKER_ID` using Docker SDK
- Assign environment variable `WORKER_ID` to each worker container
- Create dedicated RabbitMQ queue for each worker: `worker-{id}-tasks`
- Kill and replace failed workers

### 2. **Load Balancing**
- Distribute tasks intelligently across workers
- Monitor worker capacity via heartbeat responses
- Push tasks to worker-specific queues
- Ensure no worker exceeds max capacity

### 3. **Worker Health-Check**
- **Actively send** `HeartbeatRequest` to each worker at regular intervals (e.g., every 30s)
- Expect `HeartbeatResponse` with worker status and in-progress tasks
- Retry failed heartbeats for X attempts
- Mark worker as **dead/failed** if all retry attempts fail

### 4. **Failure Handling**

#### When Worker Dies (No Heartbeat Response):
```python
1. Query all tasks that were in_progress for that worker
2. Kill the dead worker container
3. Create a new replacement worker
4. Push incomplete tasks to the new worker's queue
5. Update worker registry in database
```

#### When Task Fails (Worker Reports Failure):
```python
1. Receive TaskUpdateRequest with status="failed"
2. Check retry_count for that task
3. If retry_count < MAX_RETRIES:
   - Increment retry_count
   - Re-queue task (same or different worker)
4. Else:
   - Move task to dead-letter queue
   - Log permanent failure
```

---

## 🛠️ Worker Responsibilities

### 1. **Initialization**
- Read `WORKER_ID` from environment variable
- Connect to RabbitMQ and consume from `worker-{WORKER_ID}-tasks` queue
- Start gRPC server to listen for heartbeats from Master
- Connect as gRPC client to Master for sending task updates

### 2. **Task Processing**
```python
# Poll from worker's queue
task = consume_from_queue(f"worker-{WORKER_ID}-tasks")

# Report task started
grpc_master_client.ReportTaskUpdate(
    worker_id=WORKER_ID,
    task_id=task.id,
    status="started",
    url=task.url,
    timestamp=now()
)

# Perform crawling
try:
    result = crawl(task.url, task.depth)
    
    # Send results to Frontier via gRPC
    frontier_client.SubmitCrawlData(result)
    
    # Report task completed
    grpc_master_client.ReportTaskUpdate(
        worker_id=WORKER_ID,
        task_id=task.id,
        status="completed",
        url=task.url,
        timestamp=now()
    )
except Exception as e:
    # Report task failed
    grpc_master_client.ReportTaskUpdate(
        worker_id=WORKER_ID,
        task_id=task.id,
        status="failed",
        url=task.url,
        error_message=str(e),
        timestamp=now()
    )
```

### 3. **Health Reporting**
- Run gRPC server implementing `WorkerService`
- Respond to Master's `HeartbeatRequest` with:
  - Current task count
  - Worker status (idle/busy/full)
  - List of in-progress task IDs

### 4. **Queue Configuration**
- Each worker's queue has:
  - **Max capacity:** e.g., 10 tasks per worker
  - **Retry logic:** Tasks with `retry_count` field
  - **Fair distribution:** Master ensures balanced load

---

## 🔄 Communication Flows

### Flow 1: Master → Worker (Heartbeat)
```
┌────────┐                           ┌────────┐
│ Master │                           │ Worker │
└───┬────┘                           └───┬────┘
    │                                    │
    │ gRPC: Heartbeat(timestamp)         │
    │───────────────────────────────────>│
    │                                    │
    │ HeartbeatResponse:                 │
    │  - worker_id                       │
    │  - current_task_count              │
    │  - status                          │
    │  - in_progress_task_ids            │
    │<───────────────────────────────────│
    │                                    │
```

### Flow 2: Worker → Master (Task Update)
```
┌────────┐                           ┌────────┐
│ Worker │                           │ Master │
└───┬────┘                           └───┬────┘
    │                                    │
    │ gRPC: ReportTaskUpdate             │
    │  - worker_id                       │
    │  - task_id                         │
    │  - status (started/completed/fail) │
    │───────────────────────────────────>│
    │                                    │
    │ TaskUpdateResponse (acknowledged)  │
    │<───────────────────────────────────│
    │                                    │
```

### Flow 3: Master → Worker (Task Assignment via Queue)
```
┌────────┐      ┌──────────────┐      ┌────────┐
│ Master │      │  RabbitMQ    │      │ Worker │
└───┬────┘      └──────┬───────┘      └───┬────┘
    │                  │                   │
    │ Publish task     │                   │
    │─────────────────>│                   │
    │ to worker-1-tasks│                   │
    │                  │                   │
    │                  │ Consume task      │
    │                  │<──────────────────│
    │                  │                   │
```

---

## 🏗️ gRPC Services

### MasterService (Runs on Master)
```protobuf
service MasterService {
  rpc ReportTaskUpdate(TaskUpdateRequest) returns (TaskUpdateResponse);
  rpc GetWorkerStatus(WorkerStatusRequest) returns (WorkerStatusResponse);
}
```

**Purpose:**
- Workers connect as clients to report task updates
- Optional status queries for monitoring

### WorkerService (Runs on Each Worker)
```protobuf
service WorkerService {
  rpc Heartbeat(HeartbeatRequest) returns (HeartbeatResponse);
}
```

**Purpose:**
- Master connects as client to check worker health
- Workers respond with current state and task list

---

## 📊 Data Structures

### Worker Registry (Master's Database)
```python
{
  "worker_id": "worker-1",
  "status": "active",  # active, idle, dead, error
  "created_at": 1234567890,
  "last_heartbeat": 1234567899,
  "current_task_count": 5,
  "in_progress_tasks": ["task-1", "task-2", ...],
  "total_tasks_completed": 150,
  "failed_heartbeats": 0,  # Reset on success, increment on failure
  "container_id": "docker-container-id-abc123"
}
```

### Task Queue Message Format
```json
{
  "task_id": "task-123",
  "url": "https://example.com",
  "depth": 2,
  "max_pages": 100,
  "retry_count": 0,
  "assigned_worker": "worker-1",
  "assigned_at": 1234567890
}
```

---

## ⚙️ Configuration

### Master Configuration
```python
HEARTBEAT_INTERVAL = 30  # seconds
HEARTBEAT_TIMEOUT = 5    # seconds wait for response
HEARTBEAT_MAX_RETRIES = 3

MAX_TASKS_PER_WORKER = 10
MAX_TASK_RETRIES = 3

MIN_WORKERS = 2
MAX_WORKERS = 20
SCALE_UP_THRESHOLD = 0.8  # Create new worker if 80% load
SCALE_DOWN_THRESHOLD = 0.2  # Kill worker if <20% load
```

### Worker Configuration
```python
WORKER_ID = os.getenv("WORKER_ID")  # Set by Master
MASTER_GRPC_HOST = "master:50051"
FRONTIER_GRPC_HOST = "frontier:50052"
WORKER_GRPC_PORT = 50053  # Port for Master to connect

RABBITMQ_HOST = "rabbitmq"
WORKER_QUEUE = f"worker-{WORKER_ID}-tasks"
```

---

## 🔥 Failure Scenarios

### Scenario 1: Worker Crashes Mid-Task
```
1. Master sends heartbeat → No response
2. Master retries 3 times → All fail
3. Master marks worker as "dead"
4. Master queries in_progress_tasks = ["task-1", "task-2"]
5. Master kills container (docker.kill(worker.container_id))
6. Master creates new worker: worker-X
7. Master pushes task-1, task-2 to worker-X-tasks queue
```

### Scenario 2: Task Fails on Worker
```
1. Worker encounters error while crawling
2. Worker sends ReportTaskUpdate(status="failed", error_message="...")
3. Master checks task.retry_count = 1
4. Since retry_count < MAX_RETRIES (3):
   - Master increments retry_count to 2
   - Master re-queues task to a different worker's queue
5. New worker picks up task and tries again
```

### Scenario 3: All Workers at Capacity
```
1. Master receives new task from crawl_requests queue
2. Master checks all workers: all have current_task_count = MAX_TASKS_PER_WORKER
3. Master creates new worker: worker-5
4. Master waits for worker-5 to start and send first heartbeat
5. Master assigns task to worker-5-tasks queue
```

---

## 🚀 Implementation Checklist

### Master
- [ ] Implement worker creation via Docker SDK
- [ ] Create per-worker RabbitMQ queues dynamically
- [ ] Background task: Send periodic heartbeats to all workers
- [ ] Heartbeat failure detection and retry logic
- [ ] Task re-assignment from dead workers
- [ ] Load balancing logic (assign to least busy worker)
- [ ] gRPC server for MasterService (receive task updates)
- [ ] Worker registry CRUD operations
- [ ] Auto-scaling logic

### Worker
- [ ] Read WORKER_ID from environment variable
- [ ] gRPC server for WorkerService (respond to heartbeats)
- [ ] gRPC client to Master (send task updates)
- [ ] RabbitMQ consumer for worker-specific queue
- [ ] Task processing and crawling logic
- [ ] Error handling and failure reporting
- [ ] Track in-progress tasks locally

---

## ✅ Does This Sound Good?

**YES!** This architecture is:
- ✅ **Scalable:** Workers can be added/removed dynamically
- ✅ **Resilient:** Automatic failure detection and recovery
- ✅ **Distributed:** Load balanced across multiple workers
- ✅ **Observable:** Master knows state of all workers and tasks
- ✅ **Fair:** Retry logic prevents task loss

The protobuf is now correctly structured for bidirectional communication!
