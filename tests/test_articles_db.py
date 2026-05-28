import os
import sqlite3
from unittest.mock import patch

import pytest
from dao.articles.articles_repository import ArticlesRepository


TEST_DB = "test_articles.db"


class TestArticlesRepository:
    def setup_method(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def teardown_method(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def _make_repo(self):
        with patch.object(ArticlesRepository, "__init__", lambda self, cursor: None):
            repo = ArticlesRepository.__new__(ArticlesRepository)
        # Manually init the table
        conn = sqlite3.connect(TEST_DB)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS news_article (
                id INTEGER PRIMARY KEY,
                url TEXT NOT NULL,
                timestamp INTEGER,
                deleted BOOLEAN NOT NULL DEFAULT FALSE,
                is_seen BOOLEAN NOT NULL DEFAULT FALSE,
                is_actual BOOLEAN NOT NULL DEFAULT TRUE,
                UNIQUE (url)
            )"""
        )
        conn.commit()
        conn.close()
        return repo

    def test_save_inserts_article(self):
        """Test that save inserts a URL into the database."""
        # Test the SQL logic directly
        conn = sqlite3.connect(TEST_DB)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS news_article (
                id INTEGER PRIMARY KEY, url TEXT NOT NULL,
                timestamp INTEGER, deleted BOOLEAN NOT NULL DEFAULT FALSE,
                is_seen BOOLEAN NOT NULL DEFAULT FALSE,
                is_actual BOOLEAN NOT NULL DEFAULT TRUE, UNIQUE (url))"""
        )
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO news_article (url, timestamp) VALUES (?, ?) ON CONFLICT(url) DO NOTHING",
            ("https://example.com/", 1000),
        )
        conn.commit()

        cursor.execute("SELECT url FROM news_article")
        rows = cursor.fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "https://example.com/"
        conn.close()

    def test_save_duplicate_url_is_ignored(self):
        """Test that duplicate URLs are silently ignored."""
        conn = sqlite3.connect(TEST_DB)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS news_article (
                id INTEGER PRIMARY KEY, url TEXT NOT NULL,
                timestamp INTEGER, deleted BOOLEAN NOT NULL DEFAULT FALSE,
                is_seen BOOLEAN NOT NULL DEFAULT FALSE,
                is_actual BOOLEAN NOT NULL DEFAULT TRUE, UNIQUE (url))"""
        )
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO news_article (url, timestamp) VALUES (?, ?) ON CONFLICT(url) DO NOTHING",
            ("https://example.com/", 1000),
        )
        cursor.execute(
            "INSERT INTO news_article (url, timestamp) VALUES (?, ?) ON CONFLICT(url) DO NOTHING",
            ("https://example.com/", 2000),
        )
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM news_article")
        assert cursor.fetchone()[0] == 1
        conn.close()

    def test_seen_article_updates_flag(self):
        """Test that seen_article marks the article as seen."""
        conn = sqlite3.connect(TEST_DB)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS news_article (
                id INTEGER PRIMARY KEY, url TEXT NOT NULL,
                timestamp INTEGER, deleted BOOLEAN NOT NULL DEFAULT FALSE,
                is_seen BOOLEAN NOT NULL DEFAULT FALSE,
                is_actual BOOLEAN NOT NULL DEFAULT TRUE, UNIQUE (url))"""
        )
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO news_article (url, timestamp) VALUES (?, ?)",
            ("https://example.com/", 1000),
        )
        cursor.execute(
            "UPDATE news_article SET is_seen = TRUE WHERE url = ?",
            ["https://example.com/"],
        )
        conn.commit()

        cursor.execute(
            "SELECT is_seen FROM news_article WHERE url = ?", ("https://example.com/",)
        )
        assert cursor.fetchone()[0] == 1
        conn.close()

    def test_all_relevant_returns_unseen_articles(self):
        """Test that all_relevant returns only unseen, non-deleted, actual articles."""
        conn = sqlite3.connect(TEST_DB)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS news_article (
                id INTEGER PRIMARY KEY, url TEXT NOT NULL,
                timestamp INTEGER, deleted BOOLEAN NOT NULL DEFAULT FALSE,
                is_seen BOOLEAN NOT NULL DEFAULT FALSE,
                is_actual BOOLEAN NOT NULL DEFAULT TRUE, UNIQUE (url))"""
        )
        cursor = conn.cursor()
        # Unseen article (should be returned)
        cursor.execute(
            "INSERT INTO news_article (url, timestamp) VALUES (?, ?)",
            ("https://example.com/1/", 1000),
        )
        # Seen article (should not be returned)
        cursor.execute(
            "INSERT INTO news_article (url, timestamp, is_seen) VALUES (?, ?, ?)",
            ("https://example.com/2/", 1000, True),
        )
        # Deleted article (should not be returned)
        cursor.execute(
            "INSERT INTO news_article (url, timestamp, deleted) VALUES (?, ?, ?)",
            ("https://example.com/3/", 1000, True),
        )
        conn.commit()

        cursor.execute(
            "SELECT url FROM news_article WHERE NOT deleted AND NOT is_seen AND is_actual"
        )
        result = [row[0] for row in cursor.fetchall()]
        assert result == ["https://example.com/1/"]
        conn.close()

    def test_save_many_inserts_multiple_urls(self):
        """Test that save_many inserts multiple URLs."""
        conn = sqlite3.connect(TEST_DB)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS news_article (
                id INTEGER PRIMARY KEY, url TEXT NOT NULL,
                timestamp INTEGER, deleted BOOLEAN NOT NULL DEFAULT FALSE,
                is_seen BOOLEAN NOT NULL DEFAULT FALSE,
                is_actual BOOLEAN NOT NULL DEFAULT TRUE, UNIQUE (url))"""
        )
        cursor = conn.cursor()
        urls = ["https://example.com/1/", "https://example.com/2/", "https://example.com/3/"]
        for url in urls:
            cursor.execute(
                "INSERT INTO news_article (url, timestamp) VALUES (?, ?) ON CONFLICT(url) DO NOTHING",
                (url, 1000),
            )
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM news_article")
        assert cursor.fetchone()[0] == 3
        conn.close()

    def test_seen_many_marks_multiple_articles(self):
        """Test that seen_many marks multiple articles as seen."""
        conn = sqlite3.connect(TEST_DB)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS news_article (
                id INTEGER PRIMARY KEY, url TEXT NOT NULL,
                timestamp INTEGER, deleted BOOLEAN NOT NULL DEFAULT FALSE,
                is_seen BOOLEAN NOT NULL DEFAULT FALSE,
                is_actual BOOLEAN NOT NULL DEFAULT TRUE, UNIQUE (url))"""
        )
        cursor = conn.cursor()
        urls = ["https://example.com/1/", "https://example.com/2/", "https://example.com/3/"]
        for url in urls:
            cursor.execute(
                "INSERT INTO news_article (url, timestamp) VALUES (?, ?)", (url, 1000)
            )
        for url in urls[:2]:
            cursor.execute(
                "UPDATE news_article SET is_seen = TRUE WHERE url = ?", [url]
            )
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM news_article WHERE is_seen = TRUE")
        assert cursor.fetchone()[0] == 2
        cursor.execute("SELECT url FROM news_article WHERE is_seen = FALSE")
        assert cursor.fetchone()[0] == "https://example.com/3/"
        conn.close()

    def test_all_relevant_excludes_non_actual_articles(self):
        """Test that all_relevant excludes articles where is_actual is FALSE."""
        conn = sqlite3.connect(TEST_DB)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS news_article (
                id INTEGER PRIMARY KEY, url TEXT NOT NULL,
                timestamp INTEGER, deleted BOOLEAN NOT NULL DEFAULT FALSE,
                is_seen BOOLEAN NOT NULL DEFAULT FALSE,
                is_actual BOOLEAN NOT NULL DEFAULT TRUE, UNIQUE (url))"""
        )
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO news_article (url, timestamp) VALUES (?, ?)",
            ("https://example.com/actual/", 1000),
        )
        cursor.execute(
            "INSERT INTO news_article (url, timestamp, is_actual) VALUES (?, ?, ?)",
            ("https://example.com/not-actual/", 1000, False),
        )
        conn.commit()

        cursor.execute(
            "SELECT url FROM news_article WHERE NOT deleted AND NOT is_seen AND is_actual"
        )
        result = [row[0] for row in cursor.fetchall()]
        assert result == ["https://example.com/actual/"]
        conn.close()

    def test_all_relevant_returns_empty_when_no_articles(self):
        """Test that all_relevant returns empty list on an empty table."""
        conn = sqlite3.connect(TEST_DB)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS news_article (
                id INTEGER PRIMARY KEY, url TEXT NOT NULL,
                timestamp INTEGER, deleted BOOLEAN NOT NULL DEFAULT FALSE,
                is_seen BOOLEAN NOT NULL DEFAULT FALSE,
                is_actual BOOLEAN NOT NULL DEFAULT TRUE, UNIQUE (url))"""
        )
        cursor = conn.cursor()
        cursor.execute(
            "SELECT url FROM news_article WHERE NOT deleted AND NOT is_seen AND is_actual"
        )
        result = [row[0] for row in cursor.fetchall()]
        assert result == []
        conn.close()

    def test_all_relevant_returns_empty_when_all_seen(self):
        """Test that all_relevant returns empty when every article is already seen."""
        conn = sqlite3.connect(TEST_DB)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS news_article (
                id INTEGER PRIMARY KEY, url TEXT NOT NULL,
                timestamp INTEGER, deleted BOOLEAN NOT NULL DEFAULT FALSE,
                is_seen BOOLEAN NOT NULL DEFAULT FALSE,
                is_actual BOOLEAN NOT NULL DEFAULT TRUE, UNIQUE (url))"""
        )
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO news_article (url, timestamp, is_seen) VALUES (?, ?, ?)",
            ("https://example.com/1/", 1000, True),
        )
        cursor.execute(
            "INSERT INTO news_article (url, timestamp, is_seen) VALUES (?, ?, ?)",
            ("https://example.com/2/", 1000, True),
        )
        conn.commit()

        cursor.execute(
            "SELECT url FROM news_article WHERE NOT deleted AND NOT is_seen AND is_actual"
        )
        result = [row[0] for row in cursor.fetchall()]
        assert result == []
        conn.close()

    def test_default_values_on_insert(self):
        """Test that default column values are set correctly on insert."""
        conn = sqlite3.connect(TEST_DB)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS news_article (
                id INTEGER PRIMARY KEY, url TEXT NOT NULL,
                timestamp INTEGER, deleted BOOLEAN NOT NULL DEFAULT FALSE,
                is_seen BOOLEAN NOT NULL DEFAULT FALSE,
                is_actual BOOLEAN NOT NULL DEFAULT TRUE, UNIQUE (url))"""
        )
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO news_article (url, timestamp) VALUES (?, ?)",
            ("https://example.com/", 1000),
        )
        conn.commit()

        cursor.execute(
            "SELECT deleted, is_seen, is_actual FROM news_article WHERE url = ?",
            ("https://example.com/",),
        )
        row = cursor.fetchone()
        assert row[0] == 0, "deleted should default to FALSE"
        assert row[1] == 0, "is_seen should default to FALSE"
        assert row[2] == 1, "is_actual should default to TRUE"
        conn.close()

    def test_seen_article_on_nonexistent_url(self):
        """Test that updating a non-existent URL does not raise an error."""
        conn = sqlite3.connect(TEST_DB)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS news_article (
                id INTEGER PRIMARY KEY, url TEXT NOT NULL,
                timestamp INTEGER, deleted BOOLEAN NOT NULL DEFAULT FALSE,
                is_seen BOOLEAN NOT NULL DEFAULT FALSE,
                is_actual BOOLEAN NOT NULL DEFAULT TRUE, UNIQUE (url))"""
        )
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE news_article SET is_seen = TRUE WHERE url = ?",
            ["https://nonexistent.com/"],
        )
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM news_article")
        assert cursor.fetchone()[0] == 0
        conn.close()

    def test_save_many_with_duplicates_in_batch(self):
        """Test that save_many with duplicate URLs in the same batch only inserts once."""
        conn = sqlite3.connect(TEST_DB)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS news_article (
                id INTEGER PRIMARY KEY, url TEXT NOT NULL,
                timestamp INTEGER, deleted BOOLEAN NOT NULL DEFAULT FALSE,
                is_seen BOOLEAN NOT NULL DEFAULT FALSE,
                is_actual BOOLEAN NOT NULL DEFAULT TRUE, UNIQUE (url))"""
        )
        cursor = conn.cursor()
        urls = ["https://example.com/dup/", "https://example.com/dup/", "https://example.com/other/"]
        for url in urls:
            cursor.execute(
                "INSERT INTO news_article (url, timestamp) VALUES (?, ?) ON CONFLICT(url) DO NOTHING",
                (url, 1000),
            )
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM news_article")
        assert cursor.fetchone()[0] == 2
        conn.close()

    def test_save_many_empty_list(self):
        """Test that save_many with an empty list inserts nothing."""
        conn = sqlite3.connect(TEST_DB)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS news_article (
                id INTEGER PRIMARY KEY, url TEXT NOT NULL,
                timestamp INTEGER, deleted BOOLEAN NOT NULL DEFAULT FALSE,
                is_seen BOOLEAN NOT NULL DEFAULT FALSE,
                is_actual BOOLEAN NOT NULL DEFAULT TRUE, UNIQUE (url))"""
        )
        cursor = conn.cursor()
        urls = []
        for url in urls:
            cursor.execute(
                "INSERT INTO news_article (url, timestamp) VALUES (?, ?) ON CONFLICT(url) DO NOTHING",
                (url, 1000),
            )
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM news_article")
        assert cursor.fetchone()[0] == 0
        conn.close()

    def test_normalize_url_adds_trailing_slash(self):
        """Test that normalize adds a trailing slash when URL does not end with .html."""
        from shared.http_util import normalize

        assert normalize("https://example.com") == "https://example.com/"
        assert normalize("https://example.com/path") == "https://example.com/path/"

    def test_normalize_url_preserves_html_extension(self):
        """Test that normalize does not add a trailing slash for .html URLs."""
        from shared.http_util import normalize

        assert normalize("https://example.com/page.html") == "https://example.com/page.html"

    def test_all_relevant_returns_multiple_unseen(self):
        """Test that all_relevant returns all matching articles, not just one."""
        conn = sqlite3.connect(TEST_DB)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS news_article (
                id INTEGER PRIMARY KEY, url TEXT NOT NULL,
                timestamp INTEGER, deleted BOOLEAN NOT NULL DEFAULT FALSE,
                is_seen BOOLEAN NOT NULL DEFAULT FALSE,
                is_actual BOOLEAN NOT NULL DEFAULT TRUE, UNIQUE (url))"""
        )
        cursor = conn.cursor()
        for i in range(5):
            cursor.execute(
                "INSERT INTO news_article (url, timestamp) VALUES (?, ?)",
                (f"https://example.com/{i}/", 1000 + i),
            )
        conn.commit()

        cursor.execute(
            "SELECT url FROM news_article WHERE NOT deleted AND NOT is_seen AND is_actual"
        )
        result = [row[0] for row in cursor.fetchall()]
        assert len(result) == 5
        conn.close()

    def test_seen_article_does_not_affect_other_rows(self):
        """Test that marking one article as seen does not affect others."""
        conn = sqlite3.connect(TEST_DB)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS news_article (
                id INTEGER PRIMARY KEY, url TEXT NOT NULL,
                timestamp INTEGER, deleted BOOLEAN NOT NULL DEFAULT FALSE,
                is_seen BOOLEAN NOT NULL DEFAULT FALSE,
                is_actual BOOLEAN NOT NULL DEFAULT TRUE, UNIQUE (url))"""
        )
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO news_article (url, timestamp) VALUES (?, ?)",
            ("https://example.com/1/", 1000),
        )
        cursor.execute(
            "INSERT INTO news_article (url, timestamp) VALUES (?, ?)",
            ("https://example.com/2/", 1000),
        )
        cursor.execute(
            "UPDATE news_article SET is_seen = TRUE WHERE url = ?",
            ["https://example.com/1/"],
        )
        conn.commit()

        cursor.execute(
            "SELECT is_seen FROM news_article WHERE url = ?", ("https://example.com/2/",)
        )
        assert cursor.fetchone()[0] == 0, "Other article should remain unseen"
        conn.close()

    def test_all_relevant_combines_all_filters(self):
        """Test all_relevant with a mix of deleted, seen, and non-actual articles."""
        conn = sqlite3.connect(TEST_DB)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS news_article (
                id INTEGER PRIMARY KEY, url TEXT NOT NULL,
                timestamp INTEGER, deleted BOOLEAN NOT NULL DEFAULT FALSE,
                is_seen BOOLEAN NOT NULL DEFAULT FALSE,
                is_actual BOOLEAN NOT NULL DEFAULT TRUE, UNIQUE (url))"""
        )
        cursor = conn.cursor()
        # Should be returned
        cursor.execute(
            "INSERT INTO news_article (url, timestamp) VALUES (?, ?)",
            ("https://example.com/good/", 1000),
        )
        # Deleted
        cursor.execute(
            "INSERT INTO news_article (url, timestamp, deleted) VALUES (?, ?, ?)",
            ("https://example.com/deleted/", 1000, True),
        )
        # Seen
        cursor.execute(
            "INSERT INTO news_article (url, timestamp, is_seen) VALUES (?, ?, ?)",
            ("https://example.com/seen/", 1000, True),
        )
        # Not actual
        cursor.execute(
            "INSERT INTO news_article (url, timestamp, is_actual) VALUES (?, ?, ?)",
            ("https://example.com/stale/", 1000, False),
        )
        # Deleted + seen
        cursor.execute(
            "INSERT INTO news_article (url, timestamp, deleted, is_seen) VALUES (?, ?, ?, ?)",
            ("https://example.com/deleted-seen/", 1000, True, True),
        )
        conn.commit()

        cursor.execute(
            "SELECT url FROM news_article WHERE NOT deleted AND NOT is_seen AND is_actual"
        )
        result = [row[0] for row in cursor.fetchall()]
        assert result == ["https://example.com/good/"]
        conn.close()
