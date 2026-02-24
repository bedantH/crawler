import json
import asyncio
import grpc
from shared.database.models.crawl_requests import CrawlRequest, CrawlStatus
import shared.protos.master.master_pb2 as master__pb2
import shared.protos.master.master_pb2_grpc as master_pb2_grpc
from shared.database.models.worker import WorkerStatus, Worker
from shared.database.models.task import Task, TaskStatus
from typing import override
from shared.utils import logger
from datetime import datetime
from master.core.worker_manager import WorkerManager
from master.core.task_dispatcher import TaskDispatcher
from master.infra.dead_letter import push_to_deadletter

from shared.database.engine import engine
from sqlmodel import select, update, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Any
from shared.config import MAX_TASK_RETRIES
from shared.cache.redis import get_redis

class MasterServicer(master_pb2_grpc.MasterServiceServicer):
    def __init__(self):
        self.worker_manager = WorkerManager()
        self._semaphore = asyncio.Semaphore(10)

    @override
    async def ReportTaskUpdate(
        self, request: master__pb2.TaskUpdateRequest, context: grpc.aio.ServicerContext
    ):
        logger.info("[master:grpc] ← Received task update from worker: %s", request.worker_id)
        async with self._semaphore:
            try:
                worker_id = request.worker_id
                crawl_id = request.crawl_id
                task_id = request.task_id
                status = request.status

                ALLOWED = {"assigned", "running", "failed", "completed"}

                async with AsyncSession(engine) as session:
                    select_worker_st = select(Worker).where(
                        (Worker.id == worker_id)
                        & (Worker.status != WorkerStatus.STOPPED)
                    )
                    worker = (await session.exec(select_worker_st)).first()

                    select_task_st = select(Task).where(
                        (Task.id == task_id) & (Task.worker_id == worker_id)
                    )

                    task = (await session.exec(select_task_st)).first()

                if worker is None:
                    await self.worker_manager.kill_worker(worker_id=worker_id)

                    task_dispatcher = TaskDispatcher()
                    await task_dispatcher.dispatch_by_task_id(
                        task_id=task_id, exclude_worker_id=worker_id
                    )

                    return master__pb2.TaskUpdateResponse(acknowledged=True)

                if task is None:
                    logger.warning(
                        "Task %s not found for worker %s", task_id, worker_id
                    )
                    return master__pb2.TaskUpdateResponse(acknowledged=False)

                if request.status not in ALLOWED:
                    return master__pb2.TaskUpdateResponse(acknowledged=False)

                now = datetime.utcnow()
                task_data = json.loads(str(task.payload))

                update_data: dict[str, Any] = {"status": TaskStatus(status)}
                worker_update_data = {}

                if status == "running":
                    update_data["started_at"] = now

                if status == "completed":
                    client = get_redis()

                    worker_update_data["total_tasks_completed"] = (
                        worker.total_tasks_completed + 1
                    )
                    update_data["finished_at"] = now

                    # update redis
                    await client.set(f"crawl:visited:{task_data['url']}", 'success')

                    async with AsyncSession(engine) as session:
                        select_crawl_request = select(CrawlRequest).where(CrawlRequest.id == crawl_id)
                        crawl_request = (await session.exec(select_crawl_request)).first()

                        if crawl_request is not None:
                            new_urls_completed_count = crawl_request.total_urls_completed + 1
                            remaining_count = await client.decr(f"crawl:in_flight:{crawl_id}")

                            update_crawl_data = {
                                "total_urls_completed": new_urls_completed_count,
                            }

                            if remaining_count is not None and int(remaining_count) <= 0:
                                await client.delete(f"crawl:in_flight:{crawl_id}")
                                update_crawl_data["status"] = CrawlStatus.COMPLETED

                            update_crawl_request_st = (
                                update(CrawlRequest)
                                    .where(CrawlRequest.id == crawl_id) #type: ignore
                                    .values(
                                        **update_crawl_data
                                    )    
                            )

                            await session.exec(update_crawl_request_st)
                            await session.commit()
                        else:
                            logger.error("Crawl Request not Found for the ID: %s", crawl_id)

                if status == "failed":
                    if task.retries < MAX_TASK_RETRIES:
                        update_data["retries"] = task.retries + 1

                        async with AsyncSession(engine) as session:
                            await session.exec(
                                update(Task)
                                .where(Task.id == task_id) # type: ignore
                                .where(Task.worker_id == worker_id) # type: ignore
                                .values(**update_data)
                            )
                            await session.commit()
                        
                        update_data.clear()

                        task_dispatcher = TaskDispatcher()
                        await task_dispatcher.dispatch_by_task_id(
                            task_id=task_id, exclude_worker_id=worker_id
                        )

                    else:
                        await push_to_deadletter(
                            task_id=str(task.id),
                            task_data=json.loads(str(task.payload)),
                        )
                        update_data["status"] = TaskStatus.CANCELLED

                        # decrement in-flight counter on terminal failure too
                        client = get_redis()
                        remaining_count = await client.decr(f"crawl:in_flight:{crawl_id}")
                        if remaining_count is not None and int(remaining_count) <= 0:
                            await client.delete(f"crawl:in_flight:{crawl_id}")
                            async with AsyncSession(engine) as session:
                                await session.exec(
                                    update(CrawlRequest)
                                    .where(CrawlRequest.id == crawl_id)  # type: ignore
                                    .values(status=CrawlStatus.COMPLETED)
                                )
                                await session.commit()

                async with AsyncSession(engine) as session:
                    if update_data:
                        await session.exec(
                            update(Task)
                            .where(Task.id == task_id) # type: ignore
                            .where(Task.worker_id == worker_id) # type: ignore
                            .values(**update_data)
                        )

                    if worker_update_data:
                        await session.exec(
                            update(Worker)
                            .where(Worker.id == worker_id) # type: ignore
                            .values(**worker_update_data)
                        )

                    if update_data or worker_update_data:
                        await session.commit()

                return master__pb2.TaskUpdateResponse(acknowledged=True)

            except Exception as e:
                logger.error(
                    "Error occurred when receiving task update from request: %s, %s",
                    request,
                    e,
                    exc_info=True,
                )
                return master__pb2.TaskUpdateResponse(acknowledged=False)

    @override
    async def HandleHeartbeat(
        self, request: master__pb2.HeartbeatRequest, context: grpc.aio.ServicerContext
    ):
        logger.info("[master:grpc] ← Received heartbeat from worker: %s", request.worker_id)
        async with self._semaphore:
            try:
                worker_id = request.worker_id
                status = request.status
                tasks_in_queue = request.tasks_in_queue

                async with AsyncSession(engine) as session:
                    select_worker_st = select(Worker).where(
                        (Worker.id == worker_id) & (Worker.status != WorkerStatus.FAILED)
                    )
                    worker = (await session.exec(select_worker_st)).first()

                if worker is None:
                    logger.warning("[master:grpc] Heartbeat rejected: worker %s not found or in FAILED state", worker_id)
                    return master__pb2.HeartbeatResponse(heartbeat_ack="failed")

                if status not in ["busy", "idle", "shutting_down"]:
                    logger.warning("[master:grpc] Heartbeat rejected: invalid status '%s' from worker %s", status, worker_id)
                    return master__pb2.HeartbeatResponse(heartbeat_ack="failed")

                async with AsyncSession(engine) as session:
                    update_query = (
                        update(Worker)
                        .where(Worker.id == worker_id) # type: ignore
                        .values(
                            status=WorkerStatus(status),
                            last_heartbeat=datetime.utcnow(),
                            tasks_in_queue=tasks_in_queue,
                        )
                    )

                    await session.exec(update_query)
                    await session.commit()

                return master__pb2.HeartbeatResponse(heartbeat_ack="success")
            except Exception as e:
                logger.error(
                    "Error occurred while handling heartbeat from %s: %s",
                    request,
                    e,
                    exc_info=True,
                )
                return master__pb2.HeartbeatResponse(heartbeat_ack="failed")


async def serve(stop_event: asyncio.Event):
    server = grpc.aio.server()
    master_pb2_grpc.add_MasterServiceServicer_to_server(MasterServicer(), server)

    server.add_insecure_port("[::]:50052")
    await server.start()

    logger.info("Master gRPC server started on port 50052")

    await stop_event.wait()

    logger.info("Stopping Master gRPC server...")
    await server.stop(grace=None)
    logger.info("Master gRPC server stopped.")
