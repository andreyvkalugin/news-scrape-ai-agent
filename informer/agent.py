"""
ReAct-агент информер.

Анализирует векторную базу новостей на предмет негативного (разрушительного)
контекста вокруг заданного списка компаний. Сам агент почтой не пользуется —
после завершения его работы результат разбирается и, только если найдены
проблемы, отправляется письмо через EmailClient.
"""

import os

from langchain.agents.factory import create_agent
from langchain_core.messages import HumanMessage
from langchain_core.tools import create_retriever_tool

from dao.vector.vector_repository import VectorRepository
from gigagent.custom_giga_agent import CustomGigaChat
from informer.email_client import EmailClient
from informer.tools import ALL_TOOLS

ALERT_RECIPIENT = "andrey.v.kalugin@gmail.com"

ALERT_MARKER = "STATUS: ALERT"
OK_MARKER = "STATUS: OK"

SYSTEM_PROMPT = """Ты — аналитический агент-информер. Твоя единственная задача —
мониторить новости в векторной базе данных и выявлять разрушительный (негативный)
контекст вокруг компаний из заданного списка.

Список отслеживаемых компаний: {companies}

Что считать разрушительным контекстом:
- банкротство, неплатёжеспособность, ликвидация;
- финансовые проблемы: долги, убытки, кассовый разрыв, падение выручки;
- судебные иски, штрафы, аресты счетов, расследования;
- санкции, регуляторные ограничения, отзыв лицензий;
- массовые увольнения, уход топ-менеджмента, корпоративный кризис;
- иная существенно негативная информация о компании.

Алгоритм работы:
1. Для КАЖДОЙ компании из списка сделай 3–5 запросов через `search_company_news`
   с разными формулировками (например: '<компания> банкротство',
   '<компания> долги', '<компания> иск', '<компания> санкции',
   '<компания> финансовые проблемы').
2. Проанализируй найденные документы. Засчитывай совпадение только если
   компания действительно упоминается в тексте и есть признаки разрушительного
   контекста — без выдуманных фактов.
3. Если по хотя бы одной компании из списка найден разрушительный контекст,
   подготовь краткую сводку (1–2 абзаца на компанию) с ключевыми цитатами и
   ссылками на источники.

Формат итогового ответа СТРОГО следующий и без каких-либо префиксов:
- Если найдены проблемы хотя бы у одной компании, первая строка ответа должна
  быть ровно `{alert_marker}`, затем с новой строки — сама сводка.
- Если проблем не найдено ни у одной компании, ответ должен состоять ровно из
  одной строки: `{ok_marker}`.
- Не переводи `{alert_marker}` и `{ok_marker}` на русский язык, оставь язык оригинала

Никаких других форматов ответа не используй. Если сомневаешься —
возвращай `{ok_marker}`.
"""


class RiskInformerAgent:
    def __init__(self, recipient_email: str = ALERT_RECIPIENT):
        credentials = os.getenv("GIGACHAT_CREDENTIALS")
        self._llm = CustomGigaChat(
            credentials=credentials,
            verify_ssl_certs=False,
            model="GigaChat",
            temperature=0.2,
        )
        repository = VectorRepository()
        retriever = repository.vector_store.as_retriever(search_kwargs={"k": 4})
        self._tools = [
            create_retriever_tool(
                retriever=retriever,
                name="search_company_news",
                description="ищет новости о негативных рисках, влияющих на компанию",
            ),
        ]
        self._email_client = EmailClient()
        self._recipient = recipient_email

    def analyze(self, companies: list[str] | None = None):
        """Запускает анализ векторной БД по списку компаний.

        Если по итогам работы агент сигнализирует об алерте — отправляет письмо.
        Если проблем не найдено — письмо НЕ отправляется.
        """
        if not companies:
            return "Список компаний не задан — анализ не выполнен."

        companies_str = ", ".join(companies)
        print(f"🚀 [informer] старт анализа по компаниям: {companies_str}")
        agent = create_agent(
            model=self._llm,
            tools=self._tools,
            system_prompt=SYSTEM_PROMPT.format(
                companies=companies_str,
                alert_marker=ALERT_MARKER,
                ok_marker=OK_MARKER,
            ),
        )
        result = agent.invoke(
            {
                "messages": [
                    HumanMessage(
                        content=(
                            "Проверь векторную базу новостей на наличие "
                            f"негативной информации о компаниях: {companies_str}."
                        )
                    )
                ]
            }
        )
        response = self._extract_response(result)
        print(f"📩 [informer] получен ответ агента [ {response} ]")
        self._maybe_send_alert(response, companies_str)

    @staticmethod
    def _extract_response(result: dict) -> str:
        messages = result.get("messages", [])
        for msg in reversed(messages):
            content = getattr(msg, "content", None)
            if content and not isinstance(msg, HumanMessage):
                return content
        return "Анализ завершён без ответа."

    def _maybe_send_alert(self, response: str, companies_str: str) -> None:
        if "ALERT" not in response.upper():
            return

        body = response.strip()
        if not body:
            return

        subject = f"Алерт: негативные новости ({companies_str})"
        print(f"✉️ [informer] отправка письма на {self._recipient} — {subject}")
        try:
            self._email_client.send(
                subject=subject, body=body, recipient=self._recipient
            )
        except Exception as e:
            print(f"❌ Не удалось отправить письмо: {e}")
