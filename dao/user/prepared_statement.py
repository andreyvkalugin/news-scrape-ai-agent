CREATE_USER_TABLE = """
            CREATE TABLE IF NOT EXISTS User (
            id INTEGER PRIMARY KEY,
            telegram_id TEXT NOT NULL,
            name TEXT NOT NULL,
            deleted BOOLEAN NOT NULL DEFAULT FALSE,
            UNIQUE (telegram_id)                    
            )
        """
INSERT_USER = """
            INSERT INTO User (telegram_id, name) 
            VALUES (?, ?)
            ON CONFLICT(telegram_id) DO NOTHING;
        """
ALL_USER = "SELECT name, telegram_id FROM User WHERE NOT deleted;"
