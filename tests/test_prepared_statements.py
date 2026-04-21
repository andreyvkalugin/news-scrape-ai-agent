import sqlite3

from dao.articles.prepared_statement import (
    ALL_RELEVANT_ARTICLES,
    CREATE_ARTICLES_TABLE,
    INSERT_STATEMENT,
    SEEN_ARTICLE_STATEMENT,
)
from dao.user.prepared_statement import CREATE_USER_TABLE, INSERT_USER, ALL_USER


class TestArticlePreparedStatements:
    def setup_method(self):
        self.conn = sqlite3.connect(":memory:")

    def teardown_method(self):
        self.conn.close()

    def test_create_articles_table(self):
        self.conn.execute(CREATE_ARTICLES_TABLE)
        cursor = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='news_article'"
        )
        assert cursor.fetchone() is not None

    def test_insert_statement(self):
        self.conn.execute(CREATE_ARTICLES_TABLE)
        self.conn.execute(INSERT_STATEMENT, ("https://test.com/", 1000))
        self.conn.commit()

        rows = self.conn.execute("SELECT url, timestamp FROM news_article").fetchall()
        assert rows == [("https://test.com/", 1000)]

    def test_insert_duplicate_does_nothing(self):
        self.conn.execute(CREATE_ARTICLES_TABLE)
        self.conn.execute(INSERT_STATEMENT, ("https://test.com/", 1000))
        self.conn.execute(INSERT_STATEMENT, ("https://test.com/", 2000))
        self.conn.commit()

        count = self.conn.execute("SELECT COUNT(*) FROM news_article").fetchone()[0]
        assert count == 1

    def test_seen_article_statement(self):
        self.conn.execute(CREATE_ARTICLES_TABLE)
        self.conn.execute(INSERT_STATEMENT, ("https://test.com/", 1000))
        self.conn.execute(SEEN_ARTICLE_STATEMENT, ["https://test.com/"])
        self.conn.commit()

        is_seen = self.conn.execute(
            "SELECT is_seen FROM news_article WHERE url = ?", ("https://test.com/",)
        ).fetchone()[0]
        assert is_seen == 1

    def test_all_relevant_articles(self):
        self.conn.execute(CREATE_ARTICLES_TABLE)
        self.conn.execute(INSERT_STATEMENT, ("https://test.com/1/", 1000))
        self.conn.execute(INSERT_STATEMENT, ("https://test.com/2/", 1000))
        self.conn.execute(SEEN_ARTICLE_STATEMENT, ["https://test.com/2/"])
        self.conn.commit()

        rows = [r[0] for r in self.conn.execute(ALL_RELEVANT_ARTICLES).fetchall()]
        assert rows == ["https://test.com/1/"]

    def test_default_values(self):
        self.conn.execute(CREATE_ARTICLES_TABLE)
        self.conn.execute(INSERT_STATEMENT, ("https://test.com/", 1000))
        self.conn.commit()

        row = self.conn.execute(
            "SELECT deleted, is_seen, is_actual FROM news_article"
        ).fetchone()
        assert row == (False, False, True)


class TestUserPreparedStatements:
    def setup_method(self):
        self.conn = sqlite3.connect(":memory:")

    def teardown_method(self):
        self.conn.close()

    def test_create_user_table(self):
        self.conn.execute(CREATE_USER_TABLE)
        cursor = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='User'"
        )
        assert cursor.fetchone() is not None

    def test_insert_user(self):
        self.conn.execute(CREATE_USER_TABLE)
        self.conn.execute(INSERT_USER, ("12345", "TestUser"))
        self.conn.commit()

        rows = self.conn.execute("SELECT telegram_id, name FROM User").fetchall()
        assert rows == [("12345", "TestUser")]

    def test_insert_duplicate_telegram_id_does_nothing(self):
        self.conn.execute(CREATE_USER_TABLE)
        self.conn.execute(INSERT_USER, ("12345", "User1"))
        self.conn.execute(INSERT_USER, ("12345", "User2"))
        self.conn.commit()

        count = self.conn.execute("SELECT COUNT(*) FROM User").fetchone()[0]
        assert count == 1

    def test_all_user_excludes_deleted(self):
        self.conn.execute(CREATE_USER_TABLE)
        self.conn.execute(INSERT_USER, ("111", "Active"))
        self.conn.execute(
            "INSERT INTO User (telegram_id, name, deleted) VALUES (?, ?, ?)",
            ("222", "Deleted", True),
        )
        self.conn.commit()

        rows = self.conn.execute(ALL_USER).fetchall()
        assert len(rows) == 1
        assert rows[0] == ("Active", "111")
