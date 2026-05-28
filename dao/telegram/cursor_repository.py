import functools
import sqlite3
from typing import List

from dao.telegram.prepared_statement import (
    CREATE_CURSOR_TABLE,
    UPSERT_STATEMENT,
    CHANNEL_CURSOR,
)
from sqlite3 import Connection, Cursor

from shared.db_util import closable
from shared.http_util import normalize
from shared.time_util import get_now


class CursorRepository:
    @closable(db="cursor_database.db")
    def __init__(self, cursor: Cursor):
        print("создание БД курсора для телеграм канала")
        cursor.execute(CREATE_CURSOR_TABLE)
        print("БД записей курсоров успешно создана.")

    @closable(db="cursor_database.db")
    def save(self, cursor: Cursor, channel: str, db_cursor: int):
        cursor.execute(UPSERT_STATEMENT, (channel, db_cursor, get_now()))

    @closable(db="cursor_database.db")
    def get_cursor(self, cursor: Cursor, channel: str) -> list[str]:
        row = cursor.execute(CHANNEL_CURSOR, (channel,)).fetchone()
        return row[0] if row else None
