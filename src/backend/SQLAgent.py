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

        # Used in multi-agent mode to get addtional context
        self.get_context_delegate = None

    def process(self, user_name: str, user_id: str, prompt: str,max_tokens:int=500,temperature:float=0.3,context:str=None) -> list:

        # Get additional context when in multi-agent mode
        if self.get_context_delegate:
            context = self.get_context_delegate()
        
        # Configure and exectue the completion
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
        
        # Get the SQL statement from GPT
        sql_statement = str(completion.choices[0].message.content)

        # Remove the system message
        sql_statement = sql_statement.replace("```","")
        sql_statement = sql_statement.replace("\n"," ")
        sql_statement = sql_statement.replace("sql","") 
        sql_statement = sql_statement.replace(";","")

        # Execute the SQL statement
        row_and_cols= rep.sql_executor(sql_statement)

        # Return the columns and rows
        columns = row_and_cols['columns']
        rows = row_and_cols['rows']
        return [
            ChatMessage(role='user',user_name=user_name,user_id=user_id,content=prompt,columns=[],rows=[]),
            ChatMessage(role='assistant',user_name=user_name,user_id=user_id,content=sql_statement,columns=columns,rows=rows)
        ]
