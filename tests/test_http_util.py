from shared.http_util import normalize


class TestNormalize:
    def test_url_without_html_gets_trailing_slash(self):
        assert normalize("https://example.com/news/123") == "https://example.com/news/123/"

    def test_url_with_html_stays_unchanged(self):
        assert normalize("https://example.com/page.html") == "https://example.com/page.html"

    def test_url_already_with_trailing_slash(self):
        assert normalize("https://example.com/news/") == "https://example.com/news//"

    def test_url_ending_with_html_extension(self):
        assert normalize("https://example.com/article/news.html") == "https://example.com/article/news.html"

    def test_empty_string(self):
        assert normalize("") == "/"

    def test_just_domain(self):
        assert normalize("https://example.com") == "https://example.com/"
