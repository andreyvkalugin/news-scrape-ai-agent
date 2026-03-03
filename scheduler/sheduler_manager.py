import asyncio
from sqlite3 import Connection
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
            trigger=IntervalTrigger(minutes=1),
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
        self._closable(lambda: self._run_crawler())
        print("Окончание анализа HTML.")

    def read(self):
        print("Запуск чтения HTML страниц сайтов...")
        self._closable(lambda: self._run_loader())
        print("Окончание чтения HTML.")

    def _run_loader(self):
        with asyncio.Runner() as runner:
            return runner.run(self.loader.load_news())

    def _run_crawler(self):
        with asyncio.Runner() as runner:
            runner.run(self.crawler.crawl_all())    

    def _closable(self, func):
        connection_articles = self.loader.articles_repository.new_connection()
        connection_crawler = self.crawler.articles_repository.new_connection()
        func()
        connection_articles.close()
        connection_crawler.close()

