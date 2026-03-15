import chromadb
from chromadb.api.types import GetResult
from datetime import datetime, timedelta, timezone

class Cleaner:
    CLEAN_UP_DAYS = 5

    def __init__(self):
        self.client = chromadb.PersistentClient(path="./vector_database")
        self.collection = self.client.get_or_create_collection(name="langchain")

    def cleanup(self):
        target_date = datetime.now(timezone.utc) - timedelta(days=self.CLEAN_UP_DAYS)
        self.collection.delete(
            where={"createdAt": {"$lt": int(target_date.timestamp())}}
        )
