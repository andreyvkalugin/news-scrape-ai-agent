"""
Инструменты для ReAct-агента информера.

Используются существующие методы HybridVectorRepository (search, search_by_date,
search_by_source) — новых методов в репозитории не создаём.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from langchain_core.tools import tool

from dao.vector.hybrid_vector import HybridVectorRepository

_vector_repo: Optional[HybridVectorRepository] = None


def _get_repo() -> HybridVectorRepository:
    global _vector_repo
    if _vector_repo is None:
        _vector_repo = HybridVectorRepository()
    return _vector_repo


@tool
def search_company_news(query: str) -> str:
    """
    Гибридный поиск новостей в векторной базе по заданному запросу.
    Используй для поиска любых упоминаний компании и сопутствующего контекста:
    например, '<компания> банкротство', '<компания> финансовые проблемы',
    '<компания> долги', '<компания> иск', '<компания> убытки', '<компания> санкции'.
    Возвращает до 8 наиболее релевантных фрагментов с метаданными.
    """
    docs = _get_repo().search(query, k=8)
    if not docs:
        return "По запросу ничего не найдено."
    return _format_docs(docs)


@tool
def search_company_recent_news(query: str, days: int = 14) -> str:
    """
    Поиск свежих новостей о компании за последние N дней.
    Используй когда нужно сосредоточиться на свежей информации.

    Args:
        query: тема для поиска, например '<компания> финансовые проблемы'
        days: глубина выборки в днях (по умолчанию 14)
    """
    since_ts = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())
    docs = _get_repo().search_by_date(query, since_timestamp=since_ts, k=8)
    if not docs:
        return f"За последние {days} дней по запросу ничего не найдено."
    return _format_docs(docs)


def _format_docs(docs: list) -> str:
    """Форматирование документов с метаданными для передачи агенту."""
    result = []
    for i, doc in enumerate(docs, 1):
        meta = doc.metadata
        source = meta.get("source", "неизвестный источник")
        ts = meta.get("createdAt")
        date_str = ""
        if ts:
            try:
                date_str = datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime(
                    "%d.%m.%Y"
                )
            except Exception:
                date_str = str(ts)
        header = f"[{i}] Источник: {source}"
        if date_str:
            header += f" | Дата: {date_str}"
        result.append(f"{header}\n{doc.page_content}")
    return "\n\n---\n\n".join(result)


ALL_TOOLS = [
    search_company_news,
    search_company_recent_news,
]
