from typing import List

from langchain_chroma import Chroma
from dao.articles.articles_repository import ArticlesRepository
from embedding.embedding_model import EmbeddingsSupport
from langchain_core.documents import Document

from shared.time_util import get_now
from langchain_text_splitters.character import RecursiveCharacterTextSplitter


class VectorRepository:
    """
    Класс векторной базы данных:
    """

    def __init__(self):
        print("создание векторной базы данных")
        self.vector_store = Chroma(
            embedding_function=EmbeddingsSupport(),
            persist_directory="./vector_database",
        )
        self.article_repository = ArticlesRepository()
        print("векторная БД создана.")

    def save(self, text: List[str], url: str):
        if not text:
            return
        try:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
            )
            documents = text_splitter.create_documents(
                texts=text, metadatas=[{"createdAt": get_now(), "url": url}]
            )
            self.vector_store.add_documents(documents)
            self.article_repository.seen_article(url)
        except Exception as e:
            print(
                f"В ходе сохраненния векторного представления статьи: [ {url} ] возникла ошибка.",
                e,
            )
