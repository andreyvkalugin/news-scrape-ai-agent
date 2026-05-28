import json
import os
from datetime import datetime, timedelta, timezone
from telethon import TelegramClient
from telethon.tl.types import InputMessagesFilterEmpty

from dao.telegram.cursor_repository import CursorRepository


class TelegramAdapter:
    def __init__(self):
        """Telegram adapter"""
        self.api_id = os.getenv("API_ID")
        self.api_hash = os.getenv("API_HASH")

        # база данных курсор
        self.cursor_repository = CursorRepository()

        self.client = TelegramClient(
            "me", self.api_id, self.api_hash, flood_sleep_threshold=60
        )

    async def fetch_messages(self, channel_url) -> list:
        async with self.client:
            await self.client.start()

            entity = await self.client.get_input_entity(channel_url)
            cursor = self.cursor_repository.get_cursor(channel_url)
            iter_kwargs = self.provide_iterator_config(entity, cursor)

            return [
                {
                    "id": msg.id,
                    "date": msg.date.isoformat(),
                    "sender_id": msg.sender_id,
                    "text": msg.message,
                    "views": msg.views or 0,
                }
                async for msg in self.client.iter_messages(**iter_kwargs)
                if msg.message
            ]

    def provide_iterator_config(self, entity, saved_offset_id):
        iter_kwargs = {
            "entity": entity,
            "filter": InputMessagesFilterEmpty(),
            "reverse": True,
        }

        if saved_offset_id:
            print(f"🔄 Найден сохраненный курсор: offset_id={saved_offset_id}")
            iter_kwargs["min_id"] = saved_offset_id
        else:
            two_weeks_ago = datetime.now(timezone.utc) - timedelta(days=14)
            print(
                f"🆕 Курсор не найден. Сбор за последние 2 недели (от {two_weeks_ago.strftime('%Y-%m-%d')})"
            )
            iter_kwargs["offset_date"] = two_weeks_ago
        return iter_kwargs
