from pydantic import BaseModel

class CrawlRequest(BaseModel):
    url: str # The URL to start crawling from.
    depth: int = 1 # The maximum depth of the crawl.
    max_pages: int = 100 # The maximum number of pages to crawl.
