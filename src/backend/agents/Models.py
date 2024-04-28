
from openai import AzureOpenAI
from pydantic import BaseModel
from .AgentSettings import AgentSettings

class BaseAgent:
    # This is the base class for all agents
    # it is really an interface
    def __init__(self):
        self.settings : AgentSettings
        self.client : AzureOpenAI
        self.get_context_delegate
    def process(self, user_name: str, user_id: str, prompt: str,max_tokens:int=500,temperature:float=0.3,context:str=None) -> list:
        pass
class ChatRequest(BaseModel):
    user_name:str = 'user'
    user_id: str = 'user'
    input: str
    max_tokens: int = 500
    temperature: float = 0.3

class ChatMessage(BaseModel):
    role:str
    user_name:str = ''
    user_id:str = ''
    content:str
    columns:list = []
    rows:list = []

class AISearchResult:
    def __init__(self, row:dict):
        self.searchScore = row['@search.score']
        self.rerankerScore = row['@search.rerankerScore']
        self.ckunk_id = row['chunk_id']
        self.parent_id = row['parent_id']
        self.chunk = row['chunk']
        self.title = row['title']
    def __str__(self) -> str:
        return f'{self.ckunk_id} - {self.title} - {self.chunk}'