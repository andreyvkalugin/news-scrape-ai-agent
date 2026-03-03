import asyncio

from scheduler.job import Job


class LoadJob(Job):

    def __call__(self):
        print("Запуск чтения HTML страниц сайтов...")
        self._closable(lambda: self._run_loader())
        print("Окончание чтения HTML.")

    def _run_loader(self):
        with asyncio.Runner() as runner:
            return runner.run(self.loader.load_news())
