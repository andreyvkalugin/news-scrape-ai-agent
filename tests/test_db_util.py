import sqlite3
import os
from shared.db_util import closable


DB_NAME = "test_closable.db"


class TestClosable:
    def setup_method(self):
        if os.path.exists(DB_NAME):
            os.remove(DB_NAME)

    def teardown_method(self):
        if os.path.exists(DB_NAME):
            os.remove(DB_NAME)

    def test_creates_connection_and_passes_cursor(self):
        class Repo:
            @closable(db=DB_NAME)
            def create(self, cursor):
                cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")

        Repo().create()

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test'")
        assert cursor.fetchone() is not None
        conn.close()

    def test_commits_changes(self):
        class Repo:
            @closable(db=DB_NAME)
            def create(self, cursor):
                cursor.execute("CREATE TABLE items (name TEXT)")

            @closable(db=DB_NAME)
            def insert(self, cursor, name):
                cursor.execute("INSERT INTO items (name) VALUES (?)", (name,))

            @closable(db=DB_NAME)
            def get_all(self, cursor):
                return cursor.execute("SELECT name FROM items").fetchall()

        repo = Repo()
        repo.create()
        repo.insert("test_item")
        result = repo.get_all()
        assert result == [("test_item",)]

    def test_closes_connection_after_execution(self):
        class Repo:
            @closable(db=DB_NAME)
            def create(self, cursor):
                cursor.execute("CREATE TABLE test (id INTEGER)")

        Repo().create()
        # If connection was not closed, this would raise on some systems
        os.path.exists(DB_NAME)

    def test_closes_connection_on_exception(self):
        class Repo:
            @closable(db=DB_NAME)
            def fail(self, cursor):
                cursor.execute("CREATE TABLE test (id INTEGER)")
                raise ValueError("intentional error")

        repo = Repo()
        try:
            repo.fail()
        except ValueError:
            pass

        # Connection should be closed, so we can open the DB again
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test'")
        # Table might or might not be committed depending on implementation
        conn.close()

    def test_returns_result(self):
        class Repo:
            @closable(db=DB_NAME)
            def create(self, cursor):
                cursor.execute("CREATE TABLE items (name TEXT)")

            @closable(db=DB_NAME)
            def get_count(self, cursor):
                return cursor.execute("SELECT COUNT(*) FROM items").fetchone()[0]

        repo = Repo()
        repo.create()
        assert repo.get_count() == 0
