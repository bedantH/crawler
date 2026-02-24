from meilisearch_python_sdk import AsyncClient
from shared.utils import logger


async def add_document(document: dict):
    logger.info(f"Adding document to meilisearch: {document}")

    async with AsyncClient("http://meilisearch:7700", "aSimpleMasterKey") as client:
        index = await client.create_index("documents", primary_key="id")

        try:
            await index.add_documents([document])
            logger.info(
                f"Successfully added document to meilisearch: {document.get('id')}"
            )
        except Exception as e:
            logger.error(f"Failed to add document to meilisearch: {e}")
