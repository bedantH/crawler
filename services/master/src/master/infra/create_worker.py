import docker
import os
from docker import errors as docker_errors
from shared.utils import logger
import time
import asyncio
from shared.queue.connection import MQConnection

IMAGE_NAME = "worker:latest"
DOCKER_NETWORK = os.environ.get("WORKER_NETWORK", "crawler_app-network")


def poll_running_status(container, timeout: int = 10) -> bool:
    start = time.time()

    while time.time() - start < timeout:
        try:
            container.reload()

            if container.status == "running":
                return True
        except docker_errors.NotFound:
            pass

        time.sleep(0.5)

    return False


async def create_worker_container(worker_id: str) -> bool:
    client = None
    container = None

    try:
        client = docker.from_env()

        container = await asyncio.to_thread(
            client.containers.run,
            image=IMAGE_NAME,
            name=worker_id,
            environment={
                "WORKER_ID": worker_id,
                "RABBITMQ_URL": os.environ.get("RABBITMQ_URL", ""),
                "DATABASE_URL": os.environ.get("DATABASE_URL", ""),
                "REDIS_HOST": os.environ.get("REDIS_HOST", "redis"),
                "FRONTIER_HOST": os.environ.get("FRONTIER_HOST", "frontier"),
                "FRONTIER_PORT": os.environ.get("FRONTIER_PORT", "50051"),
                "MASTER_HOST": os.environ.get("MASTER_HOST", "master"),
                "MASTER_PORT": os.environ.get("MASTER_PORT", "50052"),
            },
            network=DOCKER_NETWORK,
            detach=True,
        )

        container_is_running = await asyncio.to_thread(
            poll_running_status, container, 10
        )

        if not container_is_running:
            logger.error(
                "Container did not reach running state for worker %s", worker_id
            )
            try:
                container.remove(force=True)
            except Exception:
                pass
            return False

        try:
            from shared.queue.exchange import Exchange
            import aio_pika

            exchange_name = f"worker_{worker_id}"
            queue_name    = f"worker_{worker_id}_queue"
            routing_key   = f"worker_{worker_id}_task"

            async with MQConnection().channel() as channel:
                exchange = await channel.declare_exchange(
                    exchange_name, aio_pika.ExchangeType.DIRECT, durable=True
                )
                queue = await channel.declare_queue(queue_name, durable=True)
                await queue.bind(exchange=exchange, routing_key=routing_key)

                logger.info(
                    "Pre-declared exchange=%s queue=%s routing_key=%s for worker %s",
                    exchange_name, queue_name, routing_key, worker_id,
                )
        except Exception as e:
            logger.error(
                "Failed to declare queue for worker %s: %s", worker_id, e, exc_info=True
            )
            try:
                container.remove(force=True)
            except Exception:
                pass
            return False

        return True

    except docker_errors.ImageNotFound:
        logger.error("Docker image %s not found", IMAGE_NAME)
        return False

    except docker_errors.APIError as e:
        logger.error("Docker API error: %s", e, exc_info=True)
        try:
            if container:
                container.remove(force=True)
        except Exception:
            pass
        return False

    except Exception as e:
        logger.error(
            "Error occurred when creating a new container for worker %s: %s",
            worker_id,
            e,
            exc_info=True,
        )
        try:
            if container:
                container.remove(force=True)
        except Exception:
            pass
        return False
