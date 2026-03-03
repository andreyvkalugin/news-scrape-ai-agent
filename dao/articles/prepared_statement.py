INSERT_STATEMENT = """
            INSERT INTO News (url, timestamp) 
            VALUES (?, ?)
            ON CONFLICT(url) DO NOTHING;"""

CREATE_NEWS_TABLE = """
            CREATE TABLE IF NOT EXISTS News (
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
            UPDATE News SET is_seen = TRUE WHERE url = ?;
        """
ALL_RELEVANT = "SELECT url FROM News WHERE NOT deleted AND NOT is_seen AND is_actual;"
