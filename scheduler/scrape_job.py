import asyncio

from scheduler.job import Job
from telegram.processor import TelegramProcessor


class TelegramScrapeJob(Job):
    def __init__(self):
        self.processor = TelegramProcessor()

    async def arun(self):
        await self.processor.process_all()
