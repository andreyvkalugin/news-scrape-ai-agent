import asyncio

from informer.agent import RiskInformerAgent
from scheduler.job import Job
from scheduler.sync_job import SyncJob

COMPANIES = ["HornCo"]


class RiskInformerJob(SyncJob):
    def __init__(self):
        self.agent = RiskInformerAgent()

    def run(self):
        self.agent.analyze(COMPANIES)