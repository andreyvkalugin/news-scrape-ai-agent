from dao.telegram.cursor_repository import CursorRepository
from dao.vector.vector_repository import VectorRepository
from telegram.adapter import TelegramAdapter


class TelegramProcessor:
    channels = [
        # "https://t.me/Stroika_Glavnoe",
        "https://t.me/+KdcrG8vpye42NDAy"
    ]

    def __init__(self):
        self.adapter = TelegramAdapter()
        self.vector_repository = VectorRepository()
        self.cursor_repository = CursorRepository()

    async def process_all(self):
        for channel_url in self.channels:
            records = await self.adapter.fetch_messages(channel_url)

            if not records:
                print("📭 Новых сообщений с момента последнего запуска не обнаружено.")
                continue

            print(f"✅ Успешно собрано {len(records)} новых сообщений.")

            texts = [record["text"] for record in records if record.get("text")]
            self.vector_repository.save(texts, channel_url)

            new_cursor = records[-1]["id"]
            self.cursor_repository.save(channel_url, new_cursor)
            print(f"📌 Курсор в БД обновлен до offset_id={new_cursor}")
