import asyncio
from shared.utils import logger
from slave.entities.worker import Worker
from slave.entities.task import Task, ParsedHTML
from bs4 import BeautifulSoup

async def parser_worker(worker: Worker, stop_event: asyncio.Event):
    logger.info("Parser worker started")
    while not stop_event.is_set():
        try:
            task: Task = await asyncio.wait_for(worker.parser_queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            continue

        try:
            logger.info(f"Parser processing task: {task.url}")
            
            soup = BeautifulSoup(str(task.raw_html), 'html.parser')

            parsed_data = ParsedHTML(
                title='',
                description='',
                body='',
                headings=[],
            )
            
            # extract title
            title_tag = soup.find('title')
            parsed_data.title = title_tag.get_text().strip() if title_tag else 'No Title'

            # extract meta description if available
            description_tag = soup.find('meta', attrs={'name': 'description'})
            parsed_data.description = description_tag['content'].strip() if description_tag and 'content' in description_tag.attrs else 'No Description'

            # extract body text
            body_tag = soup.find('body')
            parsed_data.body = body_tag.get_text().strip() if body_tag else 'No Body'

            # extract headings
            for i in range(1, 7):
                heading_tags = soup.find_all(f'h{i}')
                for tag in heading_tags:
                    parsed_data.headings.append(tag.get_text().strip())
    
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=0.5)
                break
            except asyncio.TimeoutError:
                pass

            await worker.send_to_indexer(task)
        except Exception as e:
            logger.error(f"Parser failed for task {task}: {e}")
        finally:
            worker.parser_queue.task_done()
    logger.info("Parser worker shutting down")
