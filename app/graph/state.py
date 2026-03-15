"""
Определение состояния (State) графа LangGraph.

Улучшение: вместо простого списка сообщений используем расширенное состояние,
которое хранит:
- messages: история диалога
- documents: найденные документы (для оценки галлюцинаций)
- question: исходный вопрос пользователя
- rewritten_queries: варианты переформулировки
- relevance_checked: флаг — документы уже проверены на релевантность
- generation_count: счётчик попыток генерации ответа
"""
from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    # История сообщений (автоматически накапливается через add_messages)
    messages: Annotated[list, add_messages]
    # Исходный вопрос пользователя (не изменяется в процессе)
    question: str
    # Переформулированные варианты запроса для расширенного поиска
    rewritten_queries: list[str]
    # Список найденных документов (строки) для проверки галлюцинаций
    documents: list[str]
    # Флаг — были ли документы проверены на релевантность
    relevance_checked: bool
    # Счётчик попыток генерации (ограничение на рекурсию)
    generation_count: int
    # Финальный флаг — ответ прошёл проверку
    answer_validated: bool
