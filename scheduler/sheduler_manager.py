from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from cleanup.cleaner import Cleaner
from scheduler.analize_job import RiskInformerJob
from scheduler.crawl_job import CrawlJob
from scheduler.load_job import LoadJob
from scheduler.cleanup_job import CleanupJob
from scheduler.scrape_job import TelegramScrapeJob


class SchedulerManager:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.crawl_job = CrawlJob()
        self.load_job = LoadJob()
        self.cleanup_job = CleanupJob()
        self.telegram_scrape_job = TelegramScrapeJob()
        self.informer = RiskInformerJob()
        self.scheduler.add_job(
            self.crawl_job,
            trigger=IntervalTrigger(minutes=100),
            id="crawl_news",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self.load_job,
            trigger=IntervalTrigger(minutes=300),
            id="load_news",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self.cleanup_job,
            trigger=IntervalTrigger(days=Cleaner.CLEAN_UP_DAYS),
            id="clean_up",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self.telegram_scrape_job,
            trigger=IntervalTrigger(minutes=2),
            id="telegram_scrape",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self.informer,
            trigger=IntervalTrigger(minutes=1),
            id="risk_informer",
            replace_existing=True,
        )
        self.scheduler.start()
