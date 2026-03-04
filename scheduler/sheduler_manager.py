from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from scheduler.crawl_job import CrawlJob
from scheduler.load_job import LoadJob


class SchedulerManager:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.crawl_job = CrawlJob()
        self.load_job = LoadJob()
        self.scheduler.add_job(
            self.crawl_job,
            trigger=IntervalTrigger(minutes=1),
            id="crawl_news",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self.load_job,
            trigger=IntervalTrigger(minutes=2),
            id="load_news",
            replace_existing=True,
        )
        self.scheduler.start()
