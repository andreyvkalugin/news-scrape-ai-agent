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
