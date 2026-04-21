import pytest
from dao.articles.articles_repository import ArticlesRepository
from dao.articles.prepared_statement import (
    CREATE_ARTICLES_TABLE,
    INSERT_STATEMENT,
    SEEN_ARTICLE_STATEMENT,
    ALL_RELEVANT_ARTICLES,
)


@pytest.fixture
def repo(mocker):
    """Создаём ArticlesRepository с подменённым __init__, чтобы не трогать БД."""
    original_init = ArticlesRepository.__init__.__wrapped__
    mock_cursor = mocker.MagicMock()
    mocker.patch.object(ArticlesRepository, "__init__", original_init)
    instance = ArticlesRepository(mock_cursor)
    mock_cursor.reset_mock()
    return instance


def _call_unwrapped(method, *args, **kwargs):
    """Вызывает оригинальный (unwrapped) метод напрямую, минуя @closable."""
    return method.__wrapped__(method.__self__, *args, **kwargs)


class TestInit:
    def test_init_executes_create_table(self, mocker):
        mock_cursor = mocker.MagicMock()
        original_init = ArticlesRepository.__init__.__wrapped__
        mocker.patch.object(ArticlesRepository, "__init__", original_init)

        ArticlesRepository(mock_cursor)

        mock_cursor.execute.assert_called_once_with(CREATE_ARTICLES_TABLE)


class TestSave:
    def test_save_executes_insert(self, repo, mocker):
        mock_cursor = mocker.MagicMock()
        mocker.patch("dao.articles.articles_repository.normalize", return_value="http://example.com/")
        mocker.patch("dao.articles.articles_repository.get_now", return_value=100)

        _call_unwrapped(repo.save, mock_cursor, "http://example.com")

        mock_cursor.execute.assert_called_once_with(
            INSERT_STATEMENT, ("http://example.com/", 100)
        )


class TestSeenArticle:
    def test_seen_article_executes_update(self, repo, mocker):
        mock_cursor = mocker.MagicMock()

        _call_unwrapped(repo.seen_article, mock_cursor, "http://example.com")

        mock_cursor.execute.assert_called_once_with(
            SEEN_ARTICLE_STATEMENT, ["http://example.com"]
        )


class TestSaveMany:
    def test_save_many_inserts_all_urls(self, repo, mocker):
        mock_cursor = mocker.MagicMock()
        mocker.patch("dao.articles.articles_repository.normalize", side_effect=lambda u: u + "/")
        mocker.patch("dao.articles.articles_repository.get_now", return_value=200)
        urls = ["http://a.com", "http://b.com", "http://c.com"]

        _call_unwrapped(repo.save_many, mock_cursor, urls)

        assert mock_cursor.execute.call_count == 3
        mock_cursor.execute.assert_any_call(INSERT_STATEMENT, ("http://a.com/", 200))
        mock_cursor.execute.assert_any_call(INSERT_STATEMENT, ("http://b.com/", 200))
        mock_cursor.execute.assert_any_call(INSERT_STATEMENT, ("http://c.com/", 200))

    def test_save_many_empty_list(self, repo, mocker):
        mock_cursor = mocker.MagicMock()

        _call_unwrapped(repo.save_many, mock_cursor, [])

        mock_cursor.execute.assert_not_called()


class TestSeenMany:
    def test_seen_many_updates_all_urls(self, repo, mocker):
        mock_cursor = mocker.MagicMock()
        urls = ["http://a.com", "http://b.com"]

        _call_unwrapped(repo.seen_many, mock_cursor, urls)

        assert mock_cursor.execute.call_count == 2
        mock_cursor.execute.assert_any_call(SEEN_ARTICLE_STATEMENT, ["http://a.com"])
        mock_cursor.execute.assert_any_call(SEEN_ARTICLE_STATEMENT, ["http://b.com"])

    def test_seen_many_empty_list(self, repo, mocker):
        mock_cursor = mocker.MagicMock()

        _call_unwrapped(repo.seen_many, mock_cursor, [])

        mock_cursor.execute.assert_not_called()


class TestAllRelevant:
    def test_all_relevant_returns_urls(self, repo, mocker):
        mock_cursor = mocker.MagicMock()
        mock_cursor.execute.return_value.fetchall.return_value = [
            ("http://a.com",),
            ("http://b.com",),
        ]

        result = _call_unwrapped(repo.all_relevant, mock_cursor)

        mock_cursor.execute.assert_called_once_with(ALL_RELEVANT_ARTICLES)
        assert result == ["http://a.com", "http://b.com"]

    def test_all_relevant_empty(self, repo, mocker):
        mock_cursor = mocker.MagicMock()
        mock_cursor.execute.return_value.fetchall.return_value = []

        result = _call_unwrapped(repo.all_relevant, mock_cursor)

        assert result == []
