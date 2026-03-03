from crawlsupport.crawlstrategy.crawler_processor import CrawlerProcessor
from loader.news_loader import NewsLoader


class Job:
    def __init__(self):
        self.loader = NewsLoader()
        self.crawler = CrawlerProcessor()

    def _closable(self, func):  
        try:
            connection_articles = self.loader.articles_repository.new_connection()
            connection_crawler = self.crawler.articles_repository.new_connection()
            func()
        except Exception as e:
            print("исключение в ходе обработки джобы", e)
        finally:
            connection_articles.close()
            connection_crawler.close()