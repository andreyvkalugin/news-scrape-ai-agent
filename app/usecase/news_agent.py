import os

from langchain_core.messages import HumanMessage

from langchain.agents.factory import create_agent
from langchain_core.tools import create_retriever_tool
from langgraph.checkpoint.memory import MemorySaver

from app.usecase.agent_prompt import PROMPT
from gigagent.custom_giga_agent import CustomGigaChat
from chromadb.config import Settings
from langchain_chroma import Chroma

from dao.vector.vector_repository import VectorRepository
from embedding.embedding_model import EmbeddingsSupport


class NewsAgent:

    def __init__(self):
        LLM_CRED = os.getenv("GIGACHAT_CREDENTIALS")
        giga_chat = CustomGigaChat(
            credentials=LLM_CRED,
            verify_ssl_certs=False,
            model="GigaChat",
            temperature=0.6,
        )
        retriever = VectorRepository().vector_store.as_retriever(search_kwargs={"k": 4})
        chroma_retriever_tool = create_retriever_tool(
            retriever, name="news_searcher", description="news searcher"
        )
        self.agent = create_agent(
            model=giga_chat,
            tools=[chroma_retriever_tool],
            checkpointer=MemorySaver(),
            system_prompt=PROMPT,
        )

    def reply(self, message: str, user_id: int) -> str:
        result = self.agent.invoke(
            {"messages": [HumanMessage(content=message)]},
            config={"configurable": {"thread_id": user_id}},
        )
        return result["messages"][-1].content
