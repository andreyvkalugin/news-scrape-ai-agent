import re
from typing import List

from crawl4ai import CrawlResult
from crawlsupport.crawlstrategy.strategy_base import CrawlerBase


class AncbCrawler(CrawlerBase):
    """
    HTML анализатор для домена https://ancb.ru/:
    """

    def __init__(self):
        super().__init__("ancb.ru")

    def _obtain_relevant_news(self, results: List[CrawlResult]) -> List[CrawlResult]:
        try:
            news = {
                t
                for t in results
                if re.match(r"https://ancb.ru/news/read/(\d+)", t.url)
            }
            sorted_news = sorted(
                news, key=lambda item: int(item.url[26:]), reverse=True
            )
            relevant_news = self._filter_by_proximity(sorted_news, from_position=26)
            return relevant_news
        except Exception as e:
            print("исключение в ходе обработки ресурса https://ancb.ru/", e)
            return []
