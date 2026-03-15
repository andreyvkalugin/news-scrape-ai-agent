"""
Улучшенный NewsAgent.

Изменения по сравнению с оригиналом:
- Использует полноценный граф LangGraph (graph_builder.py) вместо одного узла
- ReAct-агент с 4 инструментами вместо 1
- Расширенное состояние (вопрос, документы, валидация)
- Сохраняет историю диалога по thread_id через MemorySaver
"""

import os

from langchain_core.messages import HumanMessage
from app.usecase.chatprocessor.agent_prompt import QUERY_REWRITE_PROMPT
from gigagent.custom_giga_agent import CustomGigaChat
from app.graph.graph_builder import build_graph


class NewsAgent:
    def __init__(self):
        LLM_CRED = os.getenv("GIGACHAT_CREDENTIALS")
        self._graph = build_graph()
        self._llm = CustomGigaChat(
            credentials=LLM_CRED,
            verify_ssl_certs=False,
            model="GigaChat",
            temperature=0.3,
        )

    def reply(self, text: str, thread_id: str) -> str:
        """
        Обрабатывает сообщение пользователя используя Multi-Query Retrieval и возвращает ответ агента.

        Args:
            text: текст запроса пользователя
            thread_id: уникальный идентификатор диалога (telegram_id)
        """
        rewritten_queries = self._rewrite_query(text)
        result = self._graph.invoke(
            input={
                "messages": [
                    HumanMessage(content=f"Ответь на вопросы: {rewritten_queries}")
                ],
                "question": text,
                "rewritten_queries": rewritten_queries,
                "documents": [],
                "relevance_checked": False,
                "generation_count": 0,
                "answer_validated": False,
            },
            config={"configurable": {"thread_id": thread_id}},
        )
        # Возвращаем последнее сообщение ИИ
        messages = result.get("messages", [])
        ai_messages = [
            m
            for m in messages
            if hasattr(m, "content") and not isinstance(m, HumanMessage)
        ]
        if ai_messages:
            return ai_messages[-1].content
        return "Не удалось получить ответ. Попробуйте переформулировать вопрос."

    def _rewrite_query(self, question) -> list[str]:
        """
        Переформулирует исходный вопрос пользователя в 3 варианта запроса.
        Это повышает полноту поиска — разные формулировки находят разные документы.
        """
        try:
            prompt = QUERY_REWRITE_PROMPT.format(question=question)
            response = self._llm.invoke([HumanMessage(content=prompt)])
            refrased_questions = [q.strip() for q in response.content.strip().split("\n") if q.strip()]
            # Добавляем оригинальный запрос как первый вариант
            return [question] + refrased_questions[:3]
        except Exception as e:
            print("исключение в ходе формирования комбинированного запроса к ЛЛМ", e)
            return [question]
