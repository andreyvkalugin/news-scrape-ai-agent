import functools
import sqlite3
from typing import List

from dao.articles.prepared_statement import (
    ALL_RELEVANT_ARTICLES,
    CREATE_ARTICLES_TABLE,
    INSERT_STATEMENT,
    SEEN_ARTICLE_STATEMENT,
)
from sqlite3 import Connection

from shared.db_util import closable
from shared.http_util import normalize
from shared.time_util import get_now


class ArticlesRepository:
    @closable(db="article_database.db")
    def __init__(self, cursor):
        print("создание БД регистра новостей")
        cursor.execute(CREATE_ARTICLES_TABLE)
        print("БД записей регистра новостей успешно создана.")

    @closable(db="article_database.db")
    def save(self, cursor, url: str):
        cursor.execute(INSERT_STATEMENT, (normalize(url), get_now()))

    @closable(db="article_database.db")
    def seen_article(self, cursor, url: str):
        cursor.execute(SEEN_ARTICLE_STATEMENT, [url])

    @closable(db="article_database.db")
    def save_many(self, cursor, urls: List[str]):
        now = get_now()
        for url in urls:
            cursor.execute(INSERT_STATEMENT, (normalize(url), now))

    @closable(db="article_database.db")
    def seen_many(self, cursor, urls: List[str]):
        for url in urls:
            cursor.execute(SEEN_ARTICLE_STATEMENT, [url])

    @closable(db="article_database.db")
    def all_relevant(self, cursor) -> list[str]:
        return [row[0] for row in cursor.execute(ALL_RELEVANT_ARTICLES).fetchall()]
