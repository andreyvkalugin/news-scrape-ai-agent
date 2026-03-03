from collections import deque
import telebot
from bot_reactor.auth_handler import AuthHandler
from dao.user.user import User
from dao.user.user_repository import UserRepository


class MessageHandler(AuthHandler):

    def __init__(self, bot: telebot.TeleBot):
        super().__init__(bot)

    def reply(self, message):
        if reply := self.get_auth_reply_message(message):
            self.bot.send_message(message.from_user.id, reply)
            return
        self.bot.send_message(message.from_user.id, "hj")
            
