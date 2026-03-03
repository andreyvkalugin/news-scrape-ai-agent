from bot_reactor.bot import TelegramBot
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()
    TelegramBot().polling()
