"""
Архитектура графа:
  START
    │
    ▼
  query_rewriter      ← переформулирует запрос (3 варианта)
    │
    ▼
  react_agent         ← ReAct-агент с набором инструментов
    │
    ▼
  relevance_grader    ← фильтрует нерелевантные документы
    │
    ▼
  hallucination_checker ← проверяет галлюцинации ЛЛМ
    │
    ├─ "retry" ──────────► react_agent (повторная генерация)
    │
    └─ "end" ─────────────► END
"""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.graph.nodes import NodesProvider
from app.graph.state import AgentState


def build_graph():
    """граф ответа пользователю"""
    nodes = NodesProvider()
    # --- Построение графа ---
    graph = StateGraph(AgentState)

    graph.add_node("query_rewriter", nodes.query_rewriter)
    graph.add_node("react_agent", nodes.react_node)
    graph.add_node("relevance_grader", nodes.relevance_grader)
    graph.add_node("hallucination_checker", nodes.hallucination_checker)

    # Рёбра
    graph.add_edge(START, "query_rewriter")
    graph.add_edge("query_rewriter", "react_agent")
    graph.add_edge("react_agent", "relevance_grader")
    graph.add_edge("relevance_grader", "hallucination_checker")

    # Условное ребро: повтор или конец
    graph.add_conditional_edges(
        "hallucination_checker",
        nodes.should_retry,
        {"retry": "react_agent", "end": END},
    )

    return graph.compile(checkpointer=MemorySaver())
