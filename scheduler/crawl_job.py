import asyncio

from scheduler.job import Job


class CrawlJob(Job):

    def __call__(self):
        print("Запуск анализа HTML страниц сайтов...")
        self._closable(lambda: self._run_crawler())
        print("Окончание анализа HTML.")

    def _run_crawler(self):
        with asyncio.Runner() as runner:
            runner.run(self.crawler.crawl_all())
