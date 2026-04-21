import json
import os
import requests
from typing import List

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from loader.html_crawler.extraction_strategy import GigaExtractionStrategy
from gigagent.custom_giga_agent import CustomGigaChat
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from loader.prompt import EXTRACTION_PROMPT


class Loader:
    def __init__(self):
        self._llm_cred = os.getenv("GIGACHAT_CREDENTIALS")
        self._llm_model = "GigaChat"
        self._llm = CustomGigaChat(
            credentials=self._llm_cred,
            model=self._llm_model,
            verify_ssl_certs=False,
            temperature=0.3,
        )
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    def _deep_crawl_news(self,url: str) -> str:
        """Fetch webpages aggressive and extract text content"""
        response = requests.get(url, headers=self.headers)
        html = response.text
        prompt = EXTRACTION_PROMPT.format(html=html[:12000])
        response = self._llm.invoke([HumanMessage(content=prompt)])
        return response.content

    def _rapid_crawl_news(self, url: str) -> str:
        """Fetch webpages by langchain and extract text content"""
        for doc in AsyncHtmlLoader(url).load():
            html = doc.page_content
            prompt = EXTRACTION_PROMPT.format(html=html[:8000])
            response = self._llm.invoke([HumanMessage(content=prompt)])
            return response.content

    async def _comprehensive_crawl_news(self, url: str) -> List[str]:
        try:
            async with AsyncWebCrawler(config=BrowserConfig(verbose=True)) as crawler:
                raw_news = await crawler.arun(
                    url=url,
                    config=CrawlerRunConfig(
                        word_count_threshold=1,
                        extraction_strategy=GigaExtractionStrategy(),
                        cache_mode=CacheMode.BYPASS,
                    ),
                )
                return [
                    news["text"]
                    for news in json.loads(raw_news.extracted_content)
                    if news["error"] == False
                ]
        except Exception as e:
            print(f"В ходе выполнения анализа статьи: [ {url} ] возникла ошибка.", e)
        return []
