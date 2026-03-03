from abc import ABC, abstractmethod
from typing import List

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CrawlResult
from crawl4ai import BFSDeepCrawlStrategy, DomainFilter, FilterChain
from typing import List
from crawl4ai import CrawlResult


class CrawlerBase(ABC):
    """
    Глубокий анализ HTML страницы
    """

    def __init__(self, domain: str):
        print(f"создание анализатора для домена: [ {domain} ]")
        self.domain = domain

    async def crawl(self) -> List[CrawlResult]:
        print(f"\n=== Анализ {self.domain} запущен ===")
        async with AsyncWebCrawler() as crawler:
            results: List[CrawlResult] = await crawler.arun(
                url=f"https://{self.domain}/",
                config=CrawlerRunConfig(
                    deep_crawl_strategy=self._provideStrategy(self.domain)
                ),
            )
            return self._obtain_relevant_news(results)

    @abstractmethod
    def _obtain_relevant_news(self, results: List[CrawlResult]) -> List[CrawlResult]:
        pass

    def _provideStrategy(self, domain: str) -> BFSDeepCrawlStrategy:
        filter_chain = FilterChain([DomainFilter(allowed_domains=[domain])])
        return BFSDeepCrawlStrategy(
            max_depth=1, max_pages=100, filter_chain=filter_chain
        )

    def _filter_by_proximity(
        self,
        crawl_result: List[CrawlResult],
        from_position: int,
        to_position: int = None,
        step: int = 5,
    ) -> List[CrawlResult]:
        if not crawl_result:
            return []
        previous = crawl_result[0]
        filtered = [previous]

        for current in crawl_result[1:]:
            if self._obtain_gap(current, previous, from_position, to_position) < step:
                filtered.append(current)
                previous = current
            else:
                break

        return filtered

    def _obtain_gap(
        self,
        current: CrawlResult,
        previous: CrawlResult,
        from_position: int,
        to_position: int,
    ) -> bool:
        if not to_position:
            return abs(
                int(current.url[from_position:]) - int(previous.url[from_position:])
            )
        return abs(
            int(current.url[from_position:to_position].removesuffix("-"))
            - int(previous.url[from_position:to_position].removesuffix("-"))
        )
