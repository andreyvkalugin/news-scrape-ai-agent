import re
from typing import List

from crawl4ai import CrawlResult
from crawlsupport.crawlstrategy.strategy_base import CrawlerBase


class ArdexpertCrawler(CrawlerBase):
    """
    HTML анализатор для домена https://ardexpert.ru/:
    """

    def __init__(self):
        super().__init__("ardexpert.ru")

    def _obtain_relevant_news(self, results: List[CrawlResult]) -> List[CrawlResult]:
        try:
            news = {
                t
                for t in results
                if re.match(r"https://ardexpert.ru/article/(\d+)", t.url)
            }
            soreted_news = sorted(
                news, key=lambda item: int(item.url[29:]), reverse=True
            )
            relevant_news = self._filter_by_proximity(soreted_news, from_position=29)
            return relevant_news
        except Exception as e:
            print("исключение в ходе обработки ресурса https://ardexpert.ru/", e)
            return []
