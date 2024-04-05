
from pydantic import BaseModel

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