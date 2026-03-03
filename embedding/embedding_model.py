import os
from gigachat import GigaChat
import numpy as np
from typing import List
   
class EmbeddingsSupport:
    def __init__(self):
        LLM_CRED = os.getenv('GIGACHAT_CREDENTIALS')
        self.giga_chat = GigaChat(credentials=LLM_CRED,verify_ssl_certs=False,model="GigaChat-Pro")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [t.embedding for t in self.giga_chat.embeddings(texts).data]
    
    def embed_query(self, query: str) -> List[float]:
        result = [t.embedding for t in self.giga_chat.embeddings([query]).data]
        return np.concatenate(result).tolist()