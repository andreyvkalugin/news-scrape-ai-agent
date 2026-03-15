import json
from typing import List

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from custom_crawler.extraction_strategy import GigaExtractionStrategy
from dao.articles.articles_repository import ArticlesRepository
from dao.vector.vector_repository import VectorRepository
from loader.loader import Loader

class NewsLoader(Loader):
    def __init__(self):
        super().__init__()
        self.vector_repository = VectorRepository()
        self.articles_repository = ArticlesRepository()

    async def load_news(self):
        for url in self.articles_repository.all_relevant():
            news = self._obtain_news(url)
            print(f"сохраняемые новость в векторную БД: {url}")
            self.vector_repository.save(news, url)
