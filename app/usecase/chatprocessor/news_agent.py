"""
Улучшенный NewsAgent.

Изменения по сравнению с оригиналом:
- Использует полноценный граф LangGraph (graph_builder.py) вместо одного узла
- ReAct-агент с 4 инструментами вместо 1
- Расширенное состояние (вопрос, документы, валидация)
- Сохраняет историю диалога по thread_id через MemorySaver
"""
from langchain_core.messages import HumanMessage

from app.graph.graph_builder import build_graph


class NewsAgent:
    def __init__(self):
        self._graph = build_graph()

    def reply(self, text: str, thread_id: str) -> str:
        """
        Обрабатывает сообщение пользователя и возвращает ответ агента.

        Args:
            text: текст запроса пользователя
            thread_id: уникальный идентификатор диалога (telegram_id)
        """
        config = {"configurable": {"thread_id": thread_id}}
        initial_state = {
            "messages": [HumanMessage(content=text)],
            "question": text,
            "rewritten_queries": [],
            "documents": [],
            "relevance_checked": False,
            "generation_count": 0,
            "answer_validated": False,
        }
        result = self._graph.invoke(initial_state, config=config)
        # Возвращаем последнее сообщение ИИ
        messages = result.get("messages", [])
        ai_messages = [m for m in messages if hasattr(m, "content") and not isinstance(m, HumanMessage)]
        if ai_messages:
            return ai_messages[-1].content
        return "Не удалось получить ответ. Попробуйте переформулировать вопрос."
