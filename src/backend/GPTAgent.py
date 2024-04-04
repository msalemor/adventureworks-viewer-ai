from openai import AzureOpenAI
from AgentSettings import AgentSettings
import repositories as rep

class GPTAgent:
    def __init__(self, settings = None, client = None):

        if settings is None:
            settings = AgentSettings()

        if client is None:
            client = AzureOpenAI(azure_endpoint=settings.api_endpoint, api_key=settings.api_key, api_version=settings.api_version)

        self.settings : AgentSettings = settings
        self.client : AzureOpenAI = client

    def process_prompt(self, user_name: str, user_id: str, prompt: str,max_tokens:int=500,temperature:float=0.3,context:str="") -> tuple:
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
        content = str(completion.choices[0].message.content)
        return {'role':'assistant','user_name':user_name,'user_id':user_id,'content':content,'columns':[],'rows':[]}
    

    def process_sql(self, user_name: str, user_id: str, prompt: str,max_tokens:int=500,temperature:float=0.3,schema:str=None) -> tuple:
        completion = self.client.chat.completions.create(
                model=self.settings.model_deployment,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an agent that can help generate sql statements based on the schema provided. Here is the schema:\n" + schema,
                    },
                    {
                        "role": "user",
                        "content": f"What is the SQL statement to:\n{prompt}\nOutput the SQL statement ONLY."
                    }
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
        
        #return ('assistant',user_name,user_id,str(completion.choices[0].message.content))
        content = str(completion.choices[0].message.content)
        content = content.replace("```","")
        content = content.replace("\n"," ")
        content = content.replace("sql","") 
        content = content.replace(";","")
        row_and_cols= rep.sql_executor(content)

        columns = row_and_cols['columns']
        rows = row_and_cols['rows']
        
        return {'role':'assistant','user_name':user_name,'user_id':user_id,'content':content,'columns':columns,'rows':rows}