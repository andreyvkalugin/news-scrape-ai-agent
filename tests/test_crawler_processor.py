from crawlsupport.crawlstrategy.crawler_processor import CrawlerProcessor
from crawl4ai import CrawlResult


class TestCrawlerProcessorFlatten:
    def _make_processor(self):
        proc = CrawlerProcessor.__new__(CrawlerProcessor)
        return proc

    def test_flatten_empty(self):
        proc = self._make_processor()
        assert proc._flatten([]) == []

    def test_flatten_single_list(self):
        proc = self._make_processor()
        result = proc._flatten([[1, 2, 3]])
        assert result == [1, 2, 3]

    def test_flatten_multiple_lists(self):
        proc = self._make_processor()
        result = proc._flatten([[1, 2], [3, 4], [5]])
        assert result == [1, 2, 3, 4, 5]

    def test_flatten_with_empty_sublists(self):
        proc = self._make_processor()
        result = proc._flatten([[], [1], [], [2, 3], []])
        assert result == [1, 2, 3]
