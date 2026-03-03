import asyncio
import itertools
import time
from typing import List

from crawlsupport.crawlstrategy.ancb import AncbCrawler
from crawlsupport.crawlstrategy.ardexpert import ArdexpertCrawler
from crawlsupport.crawlstrategy.ktostroit import KtostroitCrawler
from crawlsupport.crawlstrategy.rcmm import RcmmCrawler
from crawlsupport.crawlstrategy.vestnik import VestnikCrawler
from crawl4ai import CrawlResult
from dao.articles.articles_repository import ArticlesRepository


class CrawlerProcessor:
    """
    HTML анализатор для всех доменов
    """

    def __init__(self):
        self.crawlers = [
            AncbCrawler(),
            # ArdexpertCrawler(),
            # KtostroitCrawler(),
            # RcmmCrawler(),
            # VestnikCrawler(),
        ]
        self.articles_repository = ArticlesRepository()

    async def crawl_all(self):
        results = self._flatten([await crawler.crawl() for crawler in self.crawlers])
        urls = [result.url for result in results]
        self.articles_repository.save_many(urls)

    def _flatten(self, collection: List[List[CrawlResult]]) -> List[CrawlResult]:
        return list(itertools.chain.from_iterable(collection))
