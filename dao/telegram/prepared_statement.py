UPSERT_STATEMENT = """
            INSERT INTO telegram_cursor (channel, cursor, timestamp)
            VALUES (?, ?, ?)
            ON CONFLICT(channel) DO UPDATE SET
                cursor = excluded.cursor,
                timestamp = excluded.timestamp"""

CREATE_CURSOR_TABLE = """
            CREATE TABLE IF NOT EXISTS telegram_cursor (
                channel TEXT PRIMARY KEY,
                cursor INTEGER,
                timestamp INTEGER
            )
        """
CHANNEL_CURSOR = """
            SELECT cursor FROM telegram_cursor WHERE channel = ?;
        """
