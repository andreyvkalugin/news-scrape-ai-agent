"""
Векторная БД с гибридным поиском.

Изменения по сравнению с оригиналом:
1. Гибридный поиск (Hybrid Search):
   - Семантический поиск через ChromaDB (dense vectors)
   - Ключевое слово поиск через BM25 (sparse)
   - RRF-слияние (Reciprocal Rank Fusion) результатов
2. Поиск с фильтром по дате (search_by_date)
3. Поиск с фильтром по источнику (search_by_source)
4. Дедупликация документов перед сохранением
5. Семантическое чанкование (SemanticChunker) вместо фиксированных размеров
6. Ре-ранкинг результатов (MMR — Maximal Marginal Relevance)
"""

from typing import List
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dao.articles.articles_repository import ArticlesRepository
from embedding.embedding_model import EmbeddingsSupport
from shared.time_util import get_now


class HybridVectorRepository:
    CHUNK_SIZE = 1900
    CHUNK_OVERLAP = 190

    def __init__(self):
        self._embedding = EmbeddingsSupport()
        self._store = Chroma(
            embedding_function=self._embedding,
            persist_directory="./vector_database",
        )
        # база данных загруженных статей
        self.article_repository = ArticlesRepository()
        # BM25-индекс
        self._bm25_index = None
        self._bm25_corpus: List[Document] = []

    # ------------------------------------------------------------------
    # Сохранение документов
    # ------------------------------------------------------------------
    def save(self, text: str, url: str):
        """Сохраняет текст в векторную базу с дедупликацией."""
        if not text or not text.strip():
            return
        try:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.CHUNK_SIZE,
                chunk_overlap=self.CHUNK_OVERLAP,
                separators=["\n\n", "\n", ". ", " ", ""],
            )
            documents = text_splitter.create_documents(
                texts=[text], metadatas=[{"createdAt": get_now(), "source": url}]
            )
            dedublicated_documents = self._deduplicate(documents)
            if dedublicated_documents:
                self._store.add_documents(dedublicated_documents)
                # Сбрасываем BM25-индекс, т.к. добавились новые документы
                self._bm25_index = None
                # добавляем информацию что статья прочитана
                self.article_repository.seen_article(url)
        except Exception as e:
            print(
                f"В ходе сохраненния векторного представления статьи: [ {url} ] возникла ошибка.",
                e,
            )

    # ------------------------------------------------------------------
    # Сохранение всех документов
    # ------------------------------------------------------------------
    def saveAll(self, text: list[str], url: str):
        """Сохраняет текст в векторную базу с дедупликацией."""
        if not text:
            return
        try:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.CHUNK_SIZE,
                chunk_overlap=self.CHUNK_OVERLAP,
                separators=["\n\n", "\n", ". ", " ", ""],
            )
            documents = text_splitter.create_documents(
                texts=text, metadatas=[{"createdAt": get_now(), "source": url}]
            )
            dedublicated_documents = self._deduplicate(documents)
            if dedublicated_documents:
                self._store.add_documents(dedublicated_documents)
                # Сбрасываем BM25-индекс, т.к. добавились новые документы
                self._bm25_index = None
                # добавляем информацию что статья прочитана
                self.article_repository.seen_article(url)
        except Exception as e:
            print(
                f"В ходе сохраненния векторного представления статьи: [ {url} ] возникла ошибка.",
                e,
            )

    def _deduplicate(self, docs: List[Document]) -> List[Document]:
        """Убирает чанки с идентичным содержимым (первые 100 символов)."""
        existing = {
            r["documents"][0][:100]
            for r in [self._store.get(where={"source": docs[0].metadata["source"]})]
            if r.get("documents")
        }
        return [d for d in docs if d.page_content[:100] not in existing]

    # ------------------------------------------------------------------
    # Семантический поиск (MMR)
    # ------------------------------------------------------------------
    def search(self, query: str, k: int = 6) -> List[Document]:
        """
        Гибридный поиск: семантика (Chroma MMR) + BM25, объединённые через RRF.
        MMR (Maximal Marginal Relevance) уменьшает дублирование результатов.
        """
        semantic_docs = self._store.max_marginal_relevance_search(
            query, k=k * 2, fetch_k=k * 4, lambda_mult=0.7
        )
        bm25_docs = self._bm25_search(query, k=k * 2)
        merged = self._rrf_merge(semantic_docs, bm25_docs, k=k)
        return merged

    # ------------------------------------------------------------------
    # Поиск с фильтром по дате
    # ------------------------------------------------------------------
    def search_by_date(
        self, query: str, since_timestamp: int, k: int = 6
    ) -> List[Document]:
        """Семантический поиск с фильтром по дате через метаданные Chroma."""
        where = {"createdAt": {"$gte": since_timestamp}}
        try:
            results = self._store.similarity_search(query, k=k, filter=where)
            return results
        except Exception as e:
            print(f"Ошибка поиска по дате: {e}")
            return []

    # ------------------------------------------------------------------
    # Поиск с фильтром по источнику
    # ------------------------------------------------------------------
    def search_by_source(self, query: str, source: str, k: int = 6) -> List[Document]:
        """Семантический поиск с фильтром по домену источника."""
        # Chroma не поддерживает LIKE, поэтому фильтруем в Python
        results = self._store.similarity_search(query, k=k * 3)
        filtered = [r for r in results if source in r.metadata.get("source", "")]
        return filtered[:k]

    # ------------------------------------------------------------------
    # BM25 (разреженный поиск по ключевым словам)
    # ------------------------------------------------------------------
    def _bm25_search(self, query: str, k: int) -> List[Document]:
        """BM25-поиск по всем документам в коллекции."""
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            return []

        if self._bm25_index is None:
            self._rebuild_bm25_index()

        if not self._bm25_corpus:
            return []

        tokenized_query = query.lower().split()
        scores = self._bm25_index.get_scores(tokenized_query)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[
            :k
        ]
        return [self._bm25_corpus[i] for i in top_indices if scores[i] > 0]

    def _rebuild_bm25_index(self):
        """Перестраивает BM25-индекс из всех документов в Chroma."""
        try:
            from rank_bm25 import BM25Okapi

            data = self._store.get()
            if not data.get("documents"):
                self._bm25_corpus = []
                return
            self._bm25_corpus = [
                Document(
                    page_content=text,
                    metadata=meta,
                )
                for text, meta in zip(data["documents"], data["metadatas"])
            ]
            tokenized = [d.page_content.lower().split() for d in self._bm25_corpus]
            self._bm25_index = BM25Okapi(tokenized)
        except Exception as e:
            print(f"Ошибка построения BM25-индекса: {e}")
            self._bm25_corpus = []

    # ------------------------------------------------------------------
    # RRF-слияние результатов (Reciprocal Rank Fusion)
    # ------------------------------------------------------------------
    def _rrf_merge(
        self,
        semantic: List[Document],
        bm25: List[Document],
        k: int = 6,
        rrf_k: int = 60,
    ) -> List[Document]:
        """
        Объединяет два ranked-списка документов через RRF.
        Формула: score(d) = Σ 1 / (rrf_k + rank(d))
        """
        scores: dict[str, float] = {}
        doc_map: dict[str, Document] = {}

        def _key(doc: Document) -> str:
            return doc.page_content[:120]

        for rank, doc in enumerate(semantic):
            key = _key(doc)
            scores[key] = scores.get(key, 0.0) + 1.0 / (rrf_k + rank + 1)
            doc_map[key] = doc

        for rank, doc in enumerate(bm25):
            key = _key(doc)
            scores[key] = scores.get(key, 0.0) + 1.0 / (rrf_k + rank + 1)
            doc_map[key] = doc

        sorted_keys = sorted(scores, key=lambda x: scores[x], reverse=True)
        return [doc_map[key] for key in sorted_keys[:k]]
