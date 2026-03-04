from collections import deque

import telebot

from dao.user.user import User
from dao.user.user_repository import UserRepository


class AuthHandler:

    def __init__(self, bot: telebot.TeleBot):
        self.bot: telebot.TeleBot = bot
        self.repo = UserRepository()
        self.all_users: list[User] = self.repo.all()
        self.pending_user: list[int] = deque(maxlen=20)

    def get_auth_reply_message(self, message_data) -> str | None:
        message, user_id = message_data.text, message_data.from_user.id
        if any(id == user_id for id in self.pending_user):
            self._save_user(message_data)
            return f"Будем знакомы {message}"
        elif message == "мстрой":
            self.pending_user.append(user_id)
            return "Супер! Как я могу обращаться?"
        elif not any(user.telegram_id == user_id for user in self.all_users):
            return "Привет, мы не знакомы. Чтобы я мог с тобой продолжать общение, ответь пожалуйста на вопрос. С какой системой планируется интеграция АС РСП?"
        else:
            return None

    def _save_user(self, message_data):
        name, user_id = message_data.text, message_data.from_user.id
        self.repo.save(name, user_id)
        self.all_users.append(User(telegram_id=user_id, name=name))
        self.pending_user.remove(user_id)
