from abc import ABC, abstractmethod
import asyncio

from crawlsupport.crawlstrategy.crawler_processor import CrawlerProcessor
from loader.news_loader import NewsLoader


class Job(ABC):
    def __call__(self):
        print("Запуск джобы...")
        try:
            with asyncio.Runner() as runner:
                return runner.run(self.arun())
        except Exception as e:
            print("исключение в ходе обработки джобы", e)

    @abstractmethod
    async def arun():
        pass
