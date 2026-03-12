import json
from typing import List

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from custom_crawler.extraction_strategy import GigaExtractionStrategy
from dao.articles.articles_repository import ArticlesRepository
from dao.vector.vector_repository import VectorRepository

class NewsLoader:
    def __init__(self):
        self.vector_repository = VectorRepository()
        self.articles_repository = ArticlesRepository()

    async def load_news(self):
        for url in self.articles_repository.all_relevant():
            news = await self._obtain_news(url)
            print(f"сохраняемые новость в векторную БД: {url}")
            self.vector_repository.save(news, url)

    async def _obtain_news(self, url: str) -> List[str]:
        try:
            async with AsyncWebCrawler(config=BrowserConfig(verbose=True)) as crawler:
                raw_news = await crawler.arun(
                    url=url,
                    config=CrawlerRunConfig(
                        word_count_threshold=1,
                        extraction_strategy=GigaExtractionStrategy(),
                        cache_mode=CacheMode.BYPASS,
                    ),
                )
                return [
                    news["text"]
                    for news in json.loads(raw_news.extracted_content)
                    if news["error"] == False
                ]
        except Exception as e:
            print(f"В ходе выполнения анализа статьи: [ {url} ] возникла ошибка.", e)
        return []
