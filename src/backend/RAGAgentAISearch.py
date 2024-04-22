from openai import AzureOpenAI
from AgentSettings import AgentSettings
from Models import AISearchResult, ChatMessage
import json
import os
import requests
import database as rep

class RAGAgentAISearch:
    """This class is used to connect to a GPT model to submit a Prompt for Completion."""
    def __init__(self, settings = None, client = None):
        if settings is None:
            settings = AgentSettings()
        if client is None:
            client = AzureOpenAI(azure_endpoint=settings.api_endpoint, api_key=settings.api_key, api_version=settings.api_version)
        self.settings : AgentSettings = settings
        self.client : AzureOpenAI = client
        self.get_context_delegate = None
    
    @staticmethod
    def write_file(file_name:str, data:str):
        # Check file exists
        if not os.path.exists(file_name):
            with open(file_name, 'w') as f:
                f.write(data)

    def generate_docs(self):        
        # Check directory
        if not os.path.exists('rag_docs'):
            os.makedirs('rag_docs')

        customers = rep.get_top_customers_rag()
        content = ''
        for row in customers:
            # convert Row to JSON string
            json_str ={'CustomerID':row['CustomerID'],'FirstName':row['FirstName'],'LastName':row['LastName'],'City':row['City'],'StateProvince':row['StateProvince'],'CountryRegion':row['CountryRegion'],'Total':float(str(row['Total']))}            
            # append the records
            content += json.dumps(json_str) + '\n'
        # Write to json_str to a file
        self.write_file(f'rag_docs/Customers.txt',content)
            

        content = ''                
        products = rep.get_top_products_rag()
        for row in products:
            # convert Row to JSON string
            json_str ={'ProductId':row['ProductId'],'category':row['category'],'model':row['model'],'description':row['description'],'TotalQty':float(str(row['TotalQty']))}
            # Append ther ecords
            content += json.dumps(json_str) + '\n'
        # Write to json_str to a file
        self.write_file(f'rag_docs/Producs.txt',content)
            
    def __call_ai_search(self,input:str,limit:int=3):
        payload = {'search':input,
                   'vectorQueries':[
                       {
                           'text':input,
                           'kind':'text',
                           'k':limit,
                           'fields':'vector'
                       }
                   ],
                   'semanticConfiguration':self.settings.aisearch_semantic_configuration,
                   'top':limit,
                   'queryType':'semantic',
                   'select':'chunk_id,parent_id,chunk,title',
                   'queryLanguage':'en-US'                   
        }        
        req = requests.post(self.settings.aisearch_endpoint, json=payload, headers={'api-key':self.settings.aisearch_apikey})
        req.raise_for_status()
        return req.json()['value']

    def process(self, user_name: str, user_id: str, prompt: str,max_tokens:int=500,temperature:float=0.3,context:str="") -> list:
        """This method is used to process the prompt and return the completion.
        args:
            user_name: str - The name of the user
            user_id: str - The id of the user
            prompt: str - The prompt to send to GPT
            max_tokens: int - The max tokens to use in the completion
            temperature: float - The temperature to use in the completion
            context: str - The context to use in the completion
        returns:
            list - A list of ChatMessage objects"""
        
        if self.get_context_delegate:
            context = self.get_context_delegate()

        ai_results = self.__call_ai_search(prompt)        
        for ai_result in ai_results:
            line = AISearchResult(ai_result)
            context = f"{line.chunk}\n"

        # Get the completion
        completion = self.client.chat.completions.create(
                model=self.settings.gpt_model_deployment_name,
                messages=[
                    {
                        "role": "user",
                        "content": prompt +"Text: \"\"\"" + context + "\"\"\"",
                    }
                ],
                temperature=temperature
            )
        
        # Return the result
        result = str(completion.choices[0].message.content)        
        return [
            ChatMessage(role='user',user_name=user_name,user_id=user_id,content=prompt,columns=[],rows=[]),
            ChatMessage(role='assistant',user_name=user_name,user_id=user_id,content=result,columns=[],rows=[])            
        ]

    