from abc import ABC, abstractmethod

from crawlsupport.crawlstrategy.crawler_processor import CrawlerProcessor


class SyncJob(ABC):
    def __call__(self):
        print("Запуск джобы...")
        try:
            self.run()
        except Exception as e:
            print("исключение в ходе обработки джобы", e)

    @abstractmethod
    def run():
        pass
