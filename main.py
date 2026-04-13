from bot_reactor.bot import TelegramBot
from dotenv import load_dotenv
from phoenix.otel import register
from openinference.instrumentation.langchain import LangChainInstrumentor

if __name__ == "__main__":
    load_dotenv()
    tracer_provider = register(
        project_name="news-bot",
        auto_instrument=True,
    )
    LangChainInstrumentor().instrument(tracer_provider=tracer_provider)

    TelegramBot().polling()
