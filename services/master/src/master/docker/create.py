import docker
from master.infra.queue import get_mq_channel
from shared.utils import logger

IMAGE_NAME="slave:latest"

# get docker instance from docker daemon
client = docker.from_env()

def create_worker_container(uuid: str):
  try:
    # create docker using the image with name as the uuid passed
    client.containers.run(
        image=IMAGE_NAME,
        name=uuid,
        environment={ "WORKER_ID": uuid }
    )

    cnt = client.containers.get(uuid)

    if cnt.status == "running":
      channel = get_mq_channel()
      channel.queue_declare(f"{uuid}-queue")

      return True
    else:
        return False, "Failed to create the container"
  except Exception as e:
    logger.error("Error occurred when creating a new container: %s", e, exc_info=True)

    return False

   