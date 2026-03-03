import sqlite3
from typing import List

from dao.articles.prepared_statement import (
    ALL_RELEVANT,
    CREATE_NEWS_TABLE,
    INSERT_STATEMENT,
    SEEN_ARTICLE_STATEMENT,
)
from sqlite3 import Connection, Cursor

from shared.http_util import normalize
from shared.time_util import get_now


class ArticlesRepository:
    def __init__(self):
        print("создание БД регистра новостей")
        self.new_connection()
        self._execute(CREATE_NEWS_TABLE)
        self.connection.commit()
        print("БД записей регистра новостей успешно создана.")

    def save(self, url: str):
        self._execute(INSERT_STATEMENT, (normalize(url), get_now()))

    def seen_article(self, url: str):
        self._execute(SEEN_ARTICLE_STATEMENT, [url])
        self.connection.commit()

    def save_many(self, urls: List[str]):
        now = get_now()
        for url in urls:
            self._execute(INSERT_STATEMENT, (normalize(url), now))
        self.connection.commit()

    def seen_many(self, urls: List[str]):
        for url in urls:
            self._execute(SEEN_ARTICLE_STATEMENT, [url])
        self.connection.commit()

    def all_relevant(self) -> list[str]: 
        return [row[0] for row in self.connection.cursor().execute(ALL_RELEVANT).fetchall()]

    def _execute(self, sql: str, parameters=()):
        self.connection.cursor().execute(sql, parameters)

    def new_connection(self):
        self.connection: Connection = sqlite3.connect("articles_database.db")    
