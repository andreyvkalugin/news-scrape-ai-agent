"""
Набор инструментов (tools) для ИИ-агента.

Улучшения по сравнению с оригиналом:
- Добавлен поиск по дате (news_search_by_date)
- Добавлен поиск по источнику (news_search_by_source)
- Добавлен инструмент суммаризации (get_news_summary)
- Семантический поиск дополнен BM25 (гибридный поиск)
- Все инструменты возвращают метаданные (источник, дата)
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
def news_search(query: str) -> str:
    """
    Семантический поиск новостей о рынке недвижимости по смыслу запроса.
    Используй для общих вопросов без привязки к дате или источнику.
    Возвращает до 6 наиболее релевантных фрагментов новостей с метаданными.
    """
    docs = _get_repo().search(query, k=6)
    if not docs:
        return "По запросу ничего не найдено."
    return _format_docs(docs)


@tool
def news_search_by_date(query: str, days: int = 3) -> str:
    """
    Поиск новостей за последние N дней.
    Используй когда пользователь спрашивает о свежих или последних новостях.

    Args:
        query: тема для поиска
        days: количество дней назад (по умолчанию 3)
    """
    since_ts = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())
    docs = _get_repo().search_by_date(query, since_timestamp=since_ts, k=6)
    if not docs:
        return f"За последние {days} дней новостей по запросу не найдено."
    return _format_docs(docs)


@tool
def news_search_by_source(query: str, source: str) -> str:
    """
    Поиск новостей по конкретному источнику.
    Доступные источники: ancb.ru, rcmm.ru, ardexpert.ru, ktostroit.ru, vestnikstroy.ru

    Args:
        query: тема для поиска
        source: домен источника, например 'ancb.ru'
    """
    docs = _get_repo().search_by_source(query, source=source, k=6)
    if not docs:
        return f"На источнике {source} ничего не найдено по запросу."
    return _format_docs(docs)


@tool
def get_news_summary(query: str) -> str:
    """
    Получить расширенную выборку новостей (до 12 результатов) для подготовки сводного отчёта.
    Используй когда нужно дать обзор по теме, а не ответить на конкретный вопрос.

    Args:
        query: тема для сводки
    """
    docs = _get_repo().search(query, k=12)
    if not docs:
        return "Недостаточно данных для формирования сводки."
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


# Список всех инструментов для регистрации в агенте
ALL_TOOLS = [news_search, news_search_by_date, news_search_by_source, get_news_summary]
