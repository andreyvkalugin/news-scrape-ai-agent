import sqlite3
from typing import List

from dao.user.prepared_statement import (
    ALL_USER,
    CREATE_USER_TABLE,
    INSERT_USER,
)
from sqlite3 import Connection

from dao.user.user import User

class UserRepository:
    def __init__(self):
        print("создание БД пользователей")
        self.new_connection()
        self.connection.cursor().execute(CREATE_USER_TABLE)
        self.connection.commit()
        print("БД записей регистра пользователей успешно создана.")

    def save(self, name: str, telegram_id: int):
        self.connection.cursor().execute(INSERT_USER, (telegram_id, name))

    def all(self) -> list[User]:
        return [User(name=row[0], telegram_id=row[1]) for row in self.connection.cursor().execute(ALL_USER).fetchall()]
    
    def new_connection(self) -> Connection:
        self.connection: Connection = sqlite3.connect("user_database.db")
        return self.connection
