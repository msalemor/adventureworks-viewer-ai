import uvicorn
import logging
from AgentSettings import AgentSettings
from openai import AzureOpenAI
from Models import AISearchResult
from RAGAgentAISearch import RAGAgentAISearch




# Use this file mainly for easier debugging from VS Code
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)    
    
    settings = AgentSettings()
    client = AzureOpenAI(azure_endpoint=settings.api_endpoint, api_key=settings.api_key, api_version=settings.api_version)
    rag_agent = RAGAgentAISearch(settings, client)
    rag_agent.generate_docs()
    #rag_agent.process('user','user','What is the corporate location?')

    # Start the server
    uvicorn.run("main:app")