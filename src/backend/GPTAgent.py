from openai import AzureOpenAI
from AgentSettings import AgentSettings
from Models import ChatMessage
import database as rep

class GPTAgent:
    def __init__(self, settings = None, client = None):

        if settings is None:
            settings = AgentSettings()

        if client is None:
            client = AzureOpenAI(azure_endpoint=settings.api_endpoint, api_key=settings.api_key, api_version=settings.api_version)

        self.settings : AgentSettings = settings
        self.client : AzureOpenAI = client
        self.get_context_delegate = None

    def process(self, user_name: str, user_id: str, prompt: str,max_tokens:int=500,temperature:float=0.3,context:str="") -> list:
        
        if self.get_context_delegate:
            context = self.get_context_delegate()

        completion = self.client.chat.completions.create(
                model=self.settings.model_deployment,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an agent that can help answer questions about customers, products, and customer orders." ,
                    },
                    {
                        "role": "user",
                        "content": prompt +"Text: \"\"\"" + context + "\"\"\"",
                    }
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
        
        #return ('assistant',user_name,user_id,str(completion.choices[0].message.content))
        result = str(completion.choices[0].message.content)        
        output_messages = [
            ChatMessage(role='user',user_name=user_name,user_id=user_id,content=prompt,columns=[],rows=[]),
            ChatMessage(role='assistant',user_name=user_name,user_id=user_id,content=result,columns=[],rows=[])            
        ]
        return output_messages
    