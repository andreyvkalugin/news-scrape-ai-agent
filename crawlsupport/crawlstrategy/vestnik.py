import re
from typing import List

from crawl4ai import CrawlResult

from crawlsupport.crawlstrategy.strategy_base import CrawlerBase


class VestnikCrawler(CrawlerBase):
    """
    HTML анализатор для домена https://vestnikstroy.ru/:
    """

    def __init__(self):
        super().__init__("vestnikstroy.ru")

    def _obtain_relevant_news(self, results: List[CrawlResult]) -> List[CrawlResult]:
        try:
            news = {
                t
                for t in results
                if re.match(r"https://vestnikstroy.ru/articles/aktualno/", t.url)
            }
            return list(news)[:5]
        except Exception as e:
            print("исключение в ходе обработки ресурса https://vestnikstroy.ru/", e)
            return []
