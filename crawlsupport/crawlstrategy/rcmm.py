import re
from typing import List

from crawl4ai import CrawlResult
from crawlsupport.crawlstrategy.strategy_base import CrawlerBase


class RcmmCrawler(CrawlerBase):
    """
    HTML анализатор для домена https://rcmm.ru/:
    """

    def __init__(self):
        super().__init__("rcmm.ru")

    def _obtain_relevant_news(self, results: List[CrawlResult]) -> List[CrawlResult]:
        try:
            return self._get_news(results) + self._get_main_news(results)
        except Exception as e:
            print("исключение в ходе обработки ресурса https://rcmm.ru/", e)
            return []

    def _get_news(self, results: List[CrawlResult]) -> List[CrawlResult]:
        news = {
            t for t in results if re.match(r"https://rcmm.ru/novosti/(\d.*)", t.url)
        }
        sorted_news = sorted(
            news, key=lambda item: int(item.url[24:30].removesuffix("-")), reverse=True
        )
        relevant_news = self._filter_by_proximity(
            sorted_news, from_position=24, to_position=30, step=5
        )
        return relevant_news

    def _get_main_news(self, results: List[CrawlResult]) -> List[CrawlResult]:
        news = {
            t
            for t in results
            if re.match(r"https://rcmm.ru/novosti/glavnye-novosti/(\d.*)", t.url)
        }
        sorted_news = sorted(
            news, key=lambda item: int(item.url[40:46].removesuffix("-")), reverse=True
        )
        relevant_news = self._filter_by_proximity(
            sorted_news, from_position=40, to_position=46, step=5
        )
        return relevant_news
