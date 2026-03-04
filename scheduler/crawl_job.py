import asyncio

from crawlsupport.crawlstrategy.crawler_processor import CrawlerProcessor
from scheduler.job import Job


class CrawlJob(Job):
    def __init__(self):
        self.crawler = CrawlerProcessor()

    async def arun(self):
        await self.crawler.crawl_all()
