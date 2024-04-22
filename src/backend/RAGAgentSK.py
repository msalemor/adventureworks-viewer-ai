from openai import AzureOpenAI
from AgentSettings import AgentSettings
from Models import ChatMessage
import json
import database as rep
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureTextEmbedding
from semantic_kernel.core_plugins import TextMemoryPlugin
from semantic_kernel.functions import KernelFunction
from semantic_kernel.memory import SemanticTextMemory, VolatileMemoryStore

COLLECTION_ID="AdventureWorksAI"

class RAGAgentSK:
    """This class is used to connect to a GPT model to submit a Prompt for Completion."""
    def __init__(self, settings = None, client = None):
        if settings is None:
            settings = AgentSettings()
        if client is None:
            client = AzureOpenAI(azure_endpoint=settings.api_endpoint, api_key=settings.api_key, api_version=settings.api_version)
        self.settings : AgentSettings = settings
        self.client : AzureOpenAI = client
        self.get_context_delegate = None
        self.kernel = Kernel()
        self.service_id = "chat-gpt"
        self.kernel.add_service(
            AzureChatCompletion(
                deployment_name=settings.gpt_model_deployment_name,
                base_url=settings.api_endpoint,
                service_id=self.service_id,
                api_key=settings.api_key)
        )
        self.embedding_gen = AzureTextEmbedding(
            service_id="ada",
            deployment_name=settings.ada_model_deployment_name,
            endpoint=settings.api_endpoint,
            api_key=settings.api_key

        )
        self.kernel.add_service(self.embedding_gen)

        # In SK the storage can be changed to different kinds (Cosmos,Redis,AI Search)
        # this application uses RAM for storage
        self.storage=VolatileMemoryStore()
        
        self.memory=SemanticTextMemory(self.storage, embeddings_generator=self.embedding_gen)
        self.kernel.add_plugin(TextMemoryPlugin(self.memory), "TextMemoryPlugin")

    async def ingest_customer_and_products(self):
        try:
            if await self.storage.does_collection_exist(COLLECTION_ID):
                await self.storage.delete_collection(COLLECTION_ID)
            
            # customers = rep.get_top_customers_rag()
            # for row in customers:
            #     # convert Row to JSON string
            #     json_str ={'CustomerID':row['CustomerID'],'FirstName':row['FirstName'],'LastName':row['LastName'],'Total':float(str(row['Total']))}
            #     await self.populate_memory("CustomerID-"+str(row['CustomerID']),json.dumps(json_str),'Top Customers')
            
            products = rep.get_top_products_rag()
            for row in products:
                # convert Row to JSON string
                json_str ={'ProductId':row['ProductId'],'category':row['category'],'model':row['model'],'description':row['description'],'TotalQty':float(str(row['TotalQty']))}
                await self.populate_memory("ProductId"+str(row['ProductId']),json.dumps(json_str),'Top Products')
        finally:
            pass


    async def populate_memory(self, id:str, text:str,description:str) -> None:
        await self.memory.save_information(collection=COLLECTION_ID, id=id, text=text, description=description)
        

    async def search_memory_examples(self, memory: SemanticTextMemory, input:str) -> None:        
        result = await memory.search(COLLECTION_ID, input)
        print(f"Answer: {result[0].text}\n")

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

        # Get the context from the delegate, mainly used in multiagent mode
        if self.get_context_delegate:
            context = self.get_context_delegate()

        # Get the completion
        completion = self.client.chat.completions.create(
                model=self.settings.gpt_model_deployment_name,
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
        
        # Return the result
        result = str(completion.choices[0].message.content)        
        return [
            ChatMessage(role='user',user_name=user_name,user_id=user_id,content=prompt,columns=[],rows=[]),
            ChatMessage(role='assistant',user_name=user_name,user_id=user_id,content=result,columns=[],rows=[])            
        ]

    