INSERT_STATEMENT = """
            INSERT INTO news_article (url, timestamp) 
            VALUES (?, ?)
            ON CONFLICT(url) DO NOTHING;"""

CREATE_ARTICLES_TABLE = """
            CREATE TABLE IF NOT EXISTS news_article (
            id INTEGER PRIMARY KEY,
            url TEXT NOT NULL,
            timestamp INTEGER,
            deleted BOOLEAN NOT NULL DEFAULT FALSE,
            is_seen BOOLEAN NOT NULL DEFAULT FALSE,
            is_actual BOOLEAN NOT NULL DEFAULT TRUE,
            UNIQUE (url)                    
            )
        """
SEEN_ARTICLE_STATEMENT = """
            UPDATE news_article SET is_seen = TRUE WHERE url = ?;
        """
ALL_RELEVANT_ARTICLES = """
            SELECT url FROM news_article WHERE NOT deleted AND NOT is_seen AND is_actual;
        """
