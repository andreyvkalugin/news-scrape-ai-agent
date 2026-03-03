import time
import os
import telebot
from bot_reactor.message_handler import MessageHandler
from scheduler.sheduler_manager import SchedulerManager


class TelegramBot:
    BOT_CRED = os.getenv('TELEGRAM_KEY')
    _bot = telebot.TeleBot(BOT_CRED)
    _message_handler = MessageHandler(_bot)
    _sheduler = SchedulerManager()

    @_bot.message_handler(content_types=["text"])
    def get_text_messages(message):
        TelegramBot._message_handler.reply(message)

    def polling(self):
        while True:
            try:
                self._bot.polling(non_stop=True, interval=0)
            except Exception as e:
                print(e)
                time.sleep(5)
                continue
