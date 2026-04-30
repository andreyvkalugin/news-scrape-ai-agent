from dao.articles.articles_repository import ArticlesRepository
from dao.vector.hybrid_vector import HybridVectorRepository
from loader.loader import Loader

class NewsLoader(Loader):
    def __init__(self):
        super().__init__()
        self.vector_repository = HybridVectorRepository()
        self.articles_repository = ArticlesRepository()

    async def load_news(self):
        for url in self.articles_repository.all_relevant():
            news = await self._comprehensive_crawl_news(url)
            print(f"сохраняемые новость в векторную БД: {url}")
            self.vector_repository.saveAll(news, url)
