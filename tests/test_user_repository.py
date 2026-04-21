import os
import sqlite3

from dao.user.user import User


TEST_DB = "test_user.db"


class TestUserSqlLogic:
    def setup_method(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        self.conn = sqlite3.connect(TEST_DB)
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS User (
                id INTEGER PRIMARY KEY,
                telegram_id TEXT NOT NULL,
                name TEXT NOT NULL,
                deleted BOOLEAN NOT NULL DEFAULT FALSE,
                UNIQUE (telegram_id))"""
        )
        self.conn.commit()

    def teardown_method(self):
        self.conn.close()
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_insert_user(self):
        self.conn.execute(
            "INSERT INTO User (telegram_id, name) VALUES (?, ?) ON CONFLICT(telegram_id) DO NOTHING",
            ("12345", "TestUser"),
        )
        self.conn.commit()

        rows = self.conn.execute("SELECT name, telegram_id FROM User").fetchall()
        assert len(rows) == 1
        assert rows[0] == ("TestUser", "12345")

    def test_duplicate_telegram_id_ignored(self):
        self.conn.execute(
            "INSERT INTO User (telegram_id, name) VALUES (?, ?) ON CONFLICT(telegram_id) DO NOTHING",
            ("12345", "User1"),
        )
        self.conn.execute(
            "INSERT INTO User (telegram_id, name) VALUES (?, ?) ON CONFLICT(telegram_id) DO NOTHING",
            ("12345", "User2"),
        )
        self.conn.commit()

        rows = self.conn.execute("SELECT COUNT(*) FROM User").fetchone()
        assert rows[0] == 1

    def test_all_users_excludes_deleted(self):
        self.conn.execute(
            "INSERT INTO User (telegram_id, name) VALUES (?, ?)", ("111", "Active")
        )
        self.conn.execute(
            "INSERT INTO User (telegram_id, name, deleted) VALUES (?, ?, ?)",
            ("222", "Deleted", True),
        )
        self.conn.commit()

        rows = self.conn.execute(
            "SELECT name, telegram_id FROM User WHERE NOT deleted"
        ).fetchall()
        users = [User(name=row[0], telegram_id=row[1]) for row in rows]

        assert len(users) == 1
        assert users[0].name == "Active"
        assert users[0].telegram_id == "111"


class TestUserDataclass:
    def test_create_user(self):
        user = User(telegram_id=123, name="John")
        assert user.telegram_id == 123
        assert user.name == "John"

    def test_user_default_name(self):
        user = User(telegram_id=456)
        assert user.name is None

    def test_user_equality(self):
        u1 = User(telegram_id=1, name="A")
        u2 = User(telegram_id=1, name="A")
        assert u1 == u2
