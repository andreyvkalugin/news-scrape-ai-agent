"""
Узлы для ИИ-агента.

1. query_rewriter    — переформулирует запрос пользователя для лучшего поиска
2. relevance_grader  — фильтрует нерелевантные документы
3. hallucination_checker — проверяет, не галлюцинирует ли агент
4. answer_validator  — проверяет полноту ответа
5. react_agent       — основной ReAct-агент с набором инструментов
"""

import os
from typing import Literal
from app.tools.news_tools import (
    get_news_summary,
    news_search,
    news_search_by_date,
    news_search_by_source,
)
from gigagent.custom_giga_agent import CustomGigaChat
from langchain_core.messages import AIMessage, HumanMessage
from langchain.agents.factory import create_agent
from app.graph.state import AgentState
from app.usecase.chatprocessor.agent_prompt import (
    HALLUCINATION_GRADER_PROMPT,
    QUERY_REWRITE_PROMPT,
    RELEVANCE_GRADER_PROMPT,
    get_system_prompt,
)


class NodesProvider:
    def __init__(self):
        LLM_CRED = os.getenv("GIGACHAT_CREDENTIALS")
        self._llm = CustomGigaChat(
            credentials=LLM_CRED,
            verify_ssl_certs=False,
            model="GigaChat",
            temperature=0.3,
        )
        self._agent = create_agent(
            model=self._llm,
            tools=[
                news_search,
                news_search_by_date,
                news_search_by_source,
                get_news_summary,
            ],
            system_prompt=get_system_prompt(),
        )

    # ---------------------------------------------------------------------------
    # Узел 1: Переформулировка запроса
    # ---------------------------------------------------------------------------
    def query_rewriter(self, state: AgentState) -> dict:
        """
        Переформулирует исходный вопрос пользователя в 3 варианта запроса.
        Это повышает полноту поиска — разные формулировки находят разные документы.
        """
        question = state["question"]
        prompt = QUERY_REWRITE_PROMPT.format(question=question)
        response = self._llm.invoke([HumanMessage(content=prompt)])
        queries = [q.strip() for q in response.content.strip().split("\n") if q.strip()]
        # Добавляем оригинальный запрос как первый вариант
        all_queries = [question] + queries[:3]
        return {"rewritten_queries": all_queries}

    # ---------------------------------------------------------------------------
    # Узел 2: Основной ReAct-агент
    # ---------------------------------------------------------------------------
    def react_node(self, state: AgentState):
        """
        Основной узел: запускает ReAct-агент с набором инструментов.
        ReAct = Reasoning + Acting: агент рассуждает, выбирает инструмент,
        получает результат, снова рассуждает — и так до готового ответа.
        """
        messages = state["messages"]
        result = self._agent.invoke({"messages": messages})
        # Обновляем счётчик генераций
        count = state.get("generation_count", 0) + 1
        # Собираем все тексты найденных документов для проверки галлюцинаций
        docs = self._extract_tool_results(result.get("messages", []))
        return {
            "messages": result["messages"],
            "documents": docs,
            "generation_count": count,
        }

    def _extract_tool_results(self, messages: list) -> list[str]:
        """Извлекает результаты вызовов инструментов из истории сообщений."""
        docs = []
        for msg in messages:
            if hasattr(msg, "name") and msg.name in (
                "news_search",
                "news_search_by_date",
                "news_search_by_source",
                "get_news_summary",
            ):
                docs.append(str(msg.content))
        return docs

    # ---------------------------------------------------------------------------
    # Узел 3: Оценка релевантности документов
    # ---------------------------------------------------------------------------
    def relevance_grader(self, state: AgentState) -> dict:
        """
        Оценивает каждый найденный документ на релевантность вопросу.
        Нерелевантные документы отфильтровываются до генерации ответа.
        """
        question = state["question"]
        documents = state.get("documents", [])
        relevant_docs = []
        for doc in documents:
            prompt = RELEVANCE_GRADER_PROMPT.format(
                question=question, document=doc[:800]
            )
            response = self._llm.invoke([HumanMessage(content=prompt)])
            if "релевантен" in response.content.lower():
                relevant_docs.append(doc)
        return {
            "documents": relevant_docs,
            "relevance_checked": True,
        }

    # ---------------------------------------------------------------------------
    # Узел 4: Проверка галлюцинаций
    # ---------------------------------------------------------------------------
    def hallucination_checker(self, state: AgentState) -> dict:
        """
        Проверяет, соответствует ли последний ответ агента найденным документам.
        Если агент придумал факты — помечает ответ для перегенерации.
        """

        documents = state.get("documents", [])
        messages = state.get("messages", [])

        # Берём последнее сообщение ИИ
        ai_messages = [m for m in messages if isinstance(m, AIMessage)]
        if not ai_messages or not documents:
            return {"answer_validated": True}  # Нечего проверять

        last_answer = ai_messages[-1].content
        docs_text = "\n\n---\n\n".join(documents[:5])  # Берём первые 5 документов

        prompt = HALLUCINATION_GRADER_PROMPT.format(
            documents=docs_text[:3000],
            answer=last_answer[:1500],
        )
        response = self._llm.invoke([HumanMessage(content=prompt)])
        is_grounded = "обоснован" in response.content.lower()
        return {"answer_validated": is_grounded}

    # ---------------------------------------------------------------------------
    # Условные рёбра (edges) для маршрутизации графа
    # ---------------------------------------------------------------------------
    def should_retry(self, state: AgentState) -> Literal["retry", "end"]:
        """
        Решает, нужно ли перегенерировать ответ.
        Ограничение: не более 2 попыток, чтобы избежать бесконечного цикла.
        """
        validated = state.get("answer_validated", True)
        count = state.get("generation_count", 0)
        if not validated and count < 2:
            return "retry"
        return "end"
