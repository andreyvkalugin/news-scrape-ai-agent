import asyncio
import sqlite3
from typing import List
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from crawlsupport.crawlstrategy.crawler_processor import CrawlerProcessor
from loader.news_loader import NewsLoader


class SchedulerManager:
    def __init__(self):
        self.loader = NewsLoader()
        self.scheduler = BackgroundScheduler()
        self.crawler = CrawlerProcessor()
        self.scheduler.add_job(
            self.crawl,
            trigger=IntervalTrigger(minutes=5),
            id="crawl_news",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self.read,
            trigger=IntervalTrigger(minutes=240),
            id="read_news",
            replace_existing=True,
        )
        self.scheduler.start()

    def crawl(self):
        print("Запуск анализа HTML страниц сайтов...")
        self._set_thread_db_connection()
        with asyncio.Runner() as runner:
            runner.run(self.crawler.crawl_all())
        print("Окончание анализа HTML.")

    def read(self):
        print("Запуск чтения HTML страниц сайтов...")
        self._set_thread_db_connection()
        with asyncio.Runner() as runner:
            runner.run(self.loader.load_news())
        print("Окончание чтения HTML.")

    def _set_thread_db_connection(self):
        self.loader.articles_repository.new_connection()
        self.crawler.articles_repository.new_connection()
