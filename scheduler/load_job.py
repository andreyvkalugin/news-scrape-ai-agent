import asyncio

from loader.news_loader import NewsLoader
from scheduler.job import Job


class LoadJob(Job):
    def __init__(self):
        self.loader = NewsLoader()

    async def arun(self):
        await self.loader.load_news()
