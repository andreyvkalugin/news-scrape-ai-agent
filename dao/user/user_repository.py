import sqlite3
from typing import List

from dao.user.prepared_statement import (
    ALL_USER,
    CREATE_USER_TABLE,
    INSERT_USER,
)
from sqlite3 import Connection

from dao.user.user import User
from shared.db_util import closable

class UserRepository:
    @closable(db="user_database.db")
    def __init__(self, cursor):
        print("создание БД пользователей")
        cursor.execute(CREATE_USER_TABLE)
        print("БД записей регистра пользователей успешно создана.")

    @closable(db="user_database.db")
    def save(self, cursor, name: str, telegram_id: int):
        cursor.execute(INSERT_USER, (telegram_id, name))

    @closable(db="user_database.db")
    def all(self, cursor) -> list[User]:
        return [User(name=row[0], telegram_id=row[1]) for row in cursor.execute(ALL_USER).fetchall()]
