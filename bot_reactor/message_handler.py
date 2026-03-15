import telebot
from app.usecase.chatprocessor.news_agent import NewsAgent
from bot_reactor.auth_handler import AuthHandler


class MessageHandler(AuthHandler):

    def __init__(self, bot: telebot.TeleBot):
        super().__init__(bot)
        self.agent = NewsAgent()

    def reply(self, message_data):
        message, user_id = message_data.text, message_data.from_user.id
        if reply := self.get_auth_reply_message(message_data):
            self.bot.send_message(user_id, reply)
            return
        self.bot.send_message(user_id, self.agent.reply(message, user_id))
