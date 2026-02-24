import asyncio
from meilisearch_python_sdk import AsyncClient

async def main():
    try:
        async with AsyncClient("http://localhost:7700", "aSimpleMasterKey") as client:
            print("Client instantiated.")
            index = client.index("documents")
            print("Index retrieved.")
            res = await index.add_documents([{"id": "test", "title": "hello"}])
            print("Added:", res)
    except Exception as e:
        print("Error:", e)

asyncio.run(main())
