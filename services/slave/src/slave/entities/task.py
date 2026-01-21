from dataclasses import dataclass
import aio_pika
from typing import Any, Optional

@dataclass
class ParsedHTML:
    title: str
    body: str
    raw_html: str

@dataclass
class ExtractedData:
    links: list[str]
    metadata: dict

@dataclass
class Task:
    depth: int
    url: str
    message: aio_pika.IncomingMessage

    parsed: Optional[ParsedHTML] = None
    extracted: Optional[ExtractedData] = None