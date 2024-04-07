from openai import AzureOpenAI
from AgentSettings import AgentSettings
from Models import ChatMessage
import database as rep

class SQLAgent:
    def __init__(self, settings = None, client = None):

        if settings is None:
            settings = AgentSettings()

        if client is None:
            client = AzureOpenAI(azure_endpoint=settings.api_endpoint, api_key=settings.api_key, api_version=settings.api_version)

        self.settings : AgentSettings = settings
        self.client : AzureOpenAI = client
        self.get_context_delegate = None

    def process(self, user_name: str, user_id: str, prompt: str,max_tokens:int=500,temperature:float=0.3,context:str=None) -> list:
        if self.get_context_delegate:
            context = self.get_context_delegate()
        
        completion = self.client.chat.completions.create(
                model=self.settings.model_deployment,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an agent that can help generate sql statements based on the schema provided. Here is the schema:\n" + context,
                    },
                    {
                        "role": "user",
                        "content": f"What is the SQL statement to:\n{prompt}\nOutput the SQL statement ONLY."
                    }
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
        
        results = str(completion.choices[0].message.content)
        results = results.replace("```","")
        results = results.replace("\n"," ")
        results = results.replace("sql","") 
        results = results.replace(";","")
        row_and_cols= rep.sql_executor(results)

        columns = row_and_cols['columns']
        rows = row_and_cols['rows']
        output_messages = [
            ChatMessage(role='user',user_name=user_name,user_id=user_id,content=prompt,columns=[],rows=[]),
            ChatMessage(role='assistant',user_name=user_name,user_id=user_id,content=results,columns=columns,rows=rows)
        ]

        return output_messages