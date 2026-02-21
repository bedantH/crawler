from protego import Protego
from shared.config import USER_AGENT

class RobotsParser:
    def __init__(self, robots: str) -> None:
        self.rp = Protego.parse(robots)

    def can_fetch(self, url: str) -> bool:
        return self.rp.can_fetch(url, USER_AGENT)
    
    def crawl_delay(self) -> float | None:
        return self.rp.crawl_delay(USER_AGENT)