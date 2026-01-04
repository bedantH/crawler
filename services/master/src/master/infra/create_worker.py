import docker
from master.infra.queue import get_mq_channel
from shared.utils import logger
import time

IMAGE_NAME="worker:latest"

# get docker instance from docker daemon
client = docker.from_env()

def poll_running_status(container, timeout=10):
  start = time.time()
  
  while time.time() - start < timeout:
    try:
      container.reload()

      if container.status == "running":
        return True
    except docker.errors.NotFound:
      pass

    time.sleep(0.5)

  return False

def create_worker_container(uuid: str):
    try:
        # create docker using the image with name as the uuid passed
        container = client.containers.run(
            image=IMAGE_NAME,
            name=uuid,
            environment={ "WORKER_ID": uuid },
            detach=True
        )

        container_is_running = poll_running_status(container, timeout=10)

        if container_is_running:
            channel = get_mq_channel()
            channel.queue_declare(f"{uuid}-queue")
            return True
        else:
            return False, "Failed to create the container"
        
    except docker.errors.ImageNotFound:
        logger.error("Docker image %s not found", IMAGE_NAME)
        return False, "Image not found"

    except docker.errors.APIError as e:
        logger.error("Docker API error: %s", e, exc_info=True)
        return False, "Docker API error"

    except Exception as e:
        logger.error("Error occurred when creating a new container: %s", e, exc_info=True)

    return False

   