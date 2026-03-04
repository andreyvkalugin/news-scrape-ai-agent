from cleanup.cleaner import Cleaner
from scheduler.job import Job


class CleanupJob(Job):
    def __init__(self):
        self.cleaner = Cleaner()

    async def arun(self):
        self.cleaner.cleanup()