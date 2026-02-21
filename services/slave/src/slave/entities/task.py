from dataclasses import dataclass
import aio_pika
from typing import Any, Optional

@dataclass
class ParsedHTML:
    title: str
    description: Optional[str]
    body: str
    headings: list[str]

@dataclass
class ExtractedData:
    links: list[str]
    metadata: dict

@dataclass
class Task:
    task_id: str
    depth: int
    url: str
    base_url: str
    crawl_id: str
    message: aio_pika.IncomingMessage
    document_id: Optional[str] = None

    raw_html: Optional[str] = None
    parsed: Optional[ParsedHTML] = None
    extracted: Optional[ExtractedData] = None
