import logging
import os
import asyncio
import requests
import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from openai import AzureOpenAI
from kcvstore import KCVStore
from agents import AgentSettings, AgentRegistration, AgentProxy, AssistantAgent, GPTAgent, SQLAgent, RAGAgentAISearch, SQLAgent 
from agents.Models import ChatRequest

import database as rep
import dotenv
import asyncio

#region: Logging settings
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
#endregion

#region: Load App settings
dotenv.load_dotenv()
DEV_MODE = os.getenv("DEV_MODE") or "development"
OPENAPI_URL = os.getenv("OPENAPI_URL")
CORS_ORIGINS = os.getenv("CORS_ORIGINS") or "*"
#endregion

#region: Initialize the agents and the store
settings = AgentSettings()
client = AzureOpenAI(azure_endpoint=settings.api_endpoint, api_key=settings.api_key, api_version=settings.api_version)
gpt_agent = GPTAgent(settings, client)
rag_agent = RAGAgentAISearch(settings, client)
#rag_agent.generate_docs()
# def wrap_ingest():
#     asyncio.run(rag_agent.ingest_customer_and_products())

# _thread = threading.Thread(target=wrap_ingest)
# _thread.start()
# _thread.join()

sql_agent = SQLAgent(settings, client)
store = KCVStore('settings.db')
#endregion

#region: FastAPI App
rep.create_directory('wwwroot/assets/data')
app = FastAPI(openapi_url=OPENAPI_URL, title="AdventureWorks API", version="0.1.0")
#endregion

#region: FastAPI CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#endregion

#region: FastAPI APIs
@app.post("/api/reindex")
def reindex():    
    rep.export_top_customers_csv()
    logger.info("reindexed the top customers csv file")    
    rep.export_top_products_csv()
    logger.info("reindexed the top products csv files")
    return {"status": "CSV files recreated"}

@app.get("/api/counts")
def read_data():
    return rep.get_all_counts()

@app.get("/api/customers")
def read_data():
    return rep.get_customers()

@app.get("/api/customers/top")
def read_data():
    return rep.get_top_customers()

@app.get("/api/products")
def read_data():
    return rep.get_products()

@app.get("/api/products/top")
def read_data():
    return rep.get_top_products()

@app.get("/api/orders")
def read_data():
    return rep.get_order_details()

@app.post('/api/chatbot')
def chatbot(request: ChatRequest):
    return gpt_agent.process('user','user',request.input,context=rep.get_top_customers_csv_as_text()+rep.get_top_products_csv_text())

@app.post('/api/sqlbot')
def sqlbot(request: ChatRequest):
    results = sql_agent.process('user','user',request.input, context=rep.sql_schema)
    # Find the assistant message
    for result in results:
        if result.role == "assistant":
            sql_statement = result.content
            row_and_cols= rep.sql_executor(sql_statement)
            columns = row_and_cols['columns']
            rows = row_and_cols['rows']
            result.columns = columns
            result.rows = rows
    return results

@app.post('/api/rag')
def ragbot(request: ChatRequest):
    return rag_agent.process('user','user',request.input, context=rep.sql_schema)
#endregion

#region: Assistants
def reset_assistant() -> AssistantAgent:    
    store.delete('assistant','id')
    try:
        val = store.get('assistant','id')
        agent = client.beta.assistants.retrieve(val)
        assistant_agent = AssistantAgent(settings, client, "", "", "", tools_list=[], assistant=agent)
        assistant_agent.cleanup()
    except:
        pass

    assistant_agent = AssistantAgent(settings, client, 
                                    "AdventureWorks Assistant",
                                    "You are a friendly asssitant that can help answer questions about customers, orders and products using the provided information.",
                                    "wwwroot/assets/data/",
                                    [{"type": "code_interpreter"}])
    
    store.set('assistant','id',assistant_agent.assistant.id)

    #return {'status':f'assistant created {assistant_agent.assistant.id}'}
    return assistant_agent

def get_assistant_agent()->AssistantAgent:
    val = store.get('assistant','id')
    if val:
        agent = client.beta.assistants.retrieve(val)
        assistant_agent = AssistantAgent(settings, client, "", "", "", tools_list=[], assistant=agent)
        logger.info(f"Reloaded assistant {assistant_agent.assistant.id}")
    else:
        # send a bad request
        assistant_agent = reset_assistant()
    return assistant_agent

@app.delete('/api/assistants')
def delete_state():    
    reset_assistant()
    return {"status":"assistant reset"}

@app.post('/api/assistants')
def chatbot(request: ChatRequest):    
    return get_assistant_agent().process(request.user_name,request.user_id,request.input)

@app.get("/api/assistants")
def get_assistant_id():
    val = store.get('assistant','id')
    return {"assistant_id":val or "None"}

@app.get("/api/status")
def get_app_status():
    total = rep.get_db_status() + rep.get_files_status()
    
    system_down = ""    
    if rep.get_db_status() == 0:
        system_down += "Db"
    if rep.get_files_status() == 0:
        system_down += "Files"    
    
    if total ==2:
        return {"status":"Online","total":total}
    elif total ==1:
        return {"status":f"{system_down} degraded","total":total}
    elif total ==0:
        return {"status":"Offline","total":total}
    else:
        return {"status":"Unknown","total":total}

#endregion

#region: multiagent
bot_agent = GPTAgent(settings, client)
bot_agent.get_context_delegate = lambda: rep.get_top_customers_csv_as_text() + rep.get_top_products_csv_text()

sql_agent = SQLAgent(settings, client)
sql_agent.get_context_delegate = lambda: rep.sql_schema

bot_agent_registration = AgentRegistration(settings, client, "SalesIntent", "Answer questions related to customers, orders and products.", bot_agent)
sql_bot_registration = AgentRegistration(settings, client, "SqlIntent", "Generate and process SQL statement.", sql_agent)
assistant_agent = get_assistant_agent()
assistant_registration = AgentRegistration(settings, client, "AssistantIntent", "Generate chart, bars, and graphs related customers, orders, and products.", assistant_agent)
rag_registration = AgentRegistration(settings, client, "RagIntent", "Provide product maintenance and usage information.", rag_agent)

proxy = AgentProxy(settings, client, [bot_agent_registration, sql_bot_registration,assistant_registration])

@app.post('/api/multiagent')
def chatbot(request: ChatRequest):
    results = proxy.process(request.user_name,request.user_id,request.input)
    for result in results:
        if result.role == "assistant":
            sql_statement = result.content
            row_and_cols= rep.sql_executor(sql_statement)
            columns = row_and_cols['columns']
            rows = row_and_cols['rows']
            result.columns = columns
            result.rows = rows
    return results
#endregion

#region: Static Files
# Set NO_STATIC_MODE= to anything to disable serving static files
serve_files = os.getenv("SERVE_FILES") or "Yes"
if serve_files=="Yes":
    app.mount("/", StaticFiles(directory="wwwroot",html = True), name="static")
#endregion

#region: Reindex the content files
reindex_content_files = os.getenv("REINDEX_FILES") or "Yes"
if reindex_content_files=="Yes":
    reindex()
#endregion

#region: Azure Web App - Free tier keep alive
async def keep_alive():
    print("Keep alive")
    while True:
        try:
            requests.get("http://localhost:8000/api/status")
            logger.info("Keep alive")
        except:
            pass
        try:
            requests.get("http://localhost/api/status")
            logger.info("Keep alive")
        except:
            pass
        # wait for 9 minutes
        await asyncio.sleep(60*9)
        
def wrap_async_func():
    asyncio.run(keep_alive())

_thread = threading.Thread(target=wrap_async_func)
_thread.start()
#endregion