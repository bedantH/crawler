import asyncio
from shared.utils import logger
from slave.entities.worker import Worker
from slave.entities.task import Task, ParsedHTML, ExtractedData
from bs4 import BeautifulSoup
from sqlmodel.ext.asyncio.session import AsyncSession
from shared.database.engine import engine
from shared.database.models.document import Document
from slave.outbound.crawl_request import FrontierClient


def parse_html(raw_html):
    soup = BeautifulSoup(raw_html, "html.parser")
    soup.prettify()

    return soup


def extract_headings(soup):
    headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
    heading_texts = [heading.get_text(strip=True) for heading in headings]

    return heading_texts


def extract_links(base_url, soup):
    links = soup.find_all("a", href=True)
    unique_links = set()

    for link in links:
        href: str = link["href"]

        if not href.startswith("http"):
            link["href"] = base_url + href
        
        if not href.startswith("tel:") or not href.startswith("mailto:"):
            unique_links.add(link["href"].strip())

    return list(unique_links)


def extract_meta(soup):
    meta_tags = soup.find_all("meta")
    meta_info = {}

    for tag in meta_tags:
        if "name" in tag.attrs and "content" in tag.attrs:
            meta_info[tag["name"]] = tag["content"]
        elif "property" in tag.attrs and "content" in tag.attrs:
            meta_info[tag["property"]] = tag["content"]

    return meta_info


def extract_body_text(soup):
    body = soup.find("body")
    if body:
        return body.get_text(separator=" ", strip=True)

    return ""


def cleanup_tree(soup):
    for tag in soup.find_all(
        ["script", "style", "noscript", "iframe", "header", "nav", "aside"]
    ):
        tag.decompose()

    main = soup.find("main")
    if main:
        for footer in main.find_all("footer"):
            footer.decompose()

        for tag in main.select(
            '[class*="footer"], [id*="footer"], [class*="copyright"], [class*="bottom"]'
        ):
            tag.decompose()

    return soup


async def parser_worker(worker: Worker, stop_event: asyncio.Event):
    logger.info("Parser worker started")
    while not stop_event.is_set():
        try:
            task: Task = await asyncio.wait_for(worker.parser_queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            continue

        try:
            logger.info(f"Parser processing task: {task.url}")

            soup = parse_html(task.raw_html)

            parsed_data = ParsedHTML(
                title="",
                description="",
                body="",
                headings=[],
            )

            # extract headings
            headings = extract_headings(soup=soup)

            # attach base url to relative links found - however this is a bold assumption I would say
            links = extract_links(base_url=task.base_url, soup=soup)

            # meta information
            meta_info = extract_meta(soup=soup)

            # before extracting the body text, need to remove outlier tags which are not important for the index
            cleanup_tree(soup=soup)

            # extract the body
            text = extract_body_text(soup=soup)

            # extract title
            title_tag = soup.find("title")

            # this is the last sub-worker this will create the record in the DB
            # and also can sendforcrawl to the frontier
            parsed_data.title = meta_info.get(
                "og:title", title_tag.get_text().strip() if title_tag else "No Title"
            )
            parsed_data.description = meta_info.get("description", "")
            parsed_data.body = text
            parsed_data.headings = headings

            extracted_data = ExtractedData(links=links, metadata=meta_info)

            # update extracted
            task.parsed = parsed_data
            task.extracted = extracted_data

            document = Document(
                url=task.url,
                description=parsed_data.description,
                title=parsed_data.title,
                headings=parsed_data.headings,
                links=extracted_data.links,
                meta_info=extracted_data.metadata,
                text=parsed_data.body,
            )

            # send update to database to create the document
            async with AsyncSession(engine) as session:
                session.add(document)
                await session.commit()
                await session.refresh(document)

            task.document_id = str(document.id)

            # send the links
            frontier_client = FrontierClient()
            frontier_client.send_crawl_request(
                url=extracted_data.links, depth=task.depth
            )

            # update the master about the task update
            await worker.master_client.report_task_update(
                task_id=task.task_id, status="completed"
            )

            task.message.ack()

            try:
                await asyncio.wait_for(stop_event.wait(), timeout=0.5)
                break
            except asyncio.TimeoutError:
                pass
        except Exception as e:
            logger.error(f"Parser failed for task {task}: {e}")
            await worker.master_client.report_task_update(
                task_id=task.task_id, status="failed"
            )

            task.message.nack(requeue=False)
        finally:
            worker.parser_queue.task_done()

    logger.info("Parser worker shutting down")
