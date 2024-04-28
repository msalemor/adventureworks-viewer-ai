from openai import AzureOpenAI
from .AgentSettings import AgentSettings
from .Models import ChatMessage
#import database as rep

class GPTAgent:
    """This class is used to connect to a GPT model to submit a Prompt for Completion."""
    def __init__(self, settings = None, client = None):
        if settings is None:
            settings = AgentSettings()
        if client is None:
            client = AzureOpenAI(azure_endpoint=settings.api_endpoint, api_key=settings.api_key, api_version=settings.api_version)
        self.settings : AgentSettings = settings
        self.client : AzureOpenAI = client
        self.get_context_delegate = None

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

    