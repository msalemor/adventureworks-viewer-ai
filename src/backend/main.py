import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from openai import AzureOpenAI
from kcvstore import KCVStore
from AgentSettings import AgentSettings
from AssistantAgent import AssistantAgent
from GPTAgent import GPTAgent
from SQLAgent import SQLAgent
import database as rep
from AgentRegistration import AgentRegistration
from AgentProxy import AgentProxy
from Models import ChatRequest
import dotenv

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
sql_agent = SQLAgent(settings, client)
store = KCVStore('settings.db')
#endregion

app = FastAPI(openapi_url=OPENAPI_URL, title="AdventureWorks API", version="0.1.0")

#region: CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#endregion

#region: API
@app.post("/api/reindex")
def reindex():    
    rep.export_top_customers_csv()
    logger.info("reindexing the top customers csv file")    
    rep.export_top_products_csv()
    logger.info("reindexed the top products csv files")
    return {"status": "reindex"}

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

@app.get("/api/products/sold")
def read_data():
    return rep.get_top_products()

@app.get("/api/orders")
def read_data():
    return rep.get_order_details()

@app.get("/api/sales/count")
def read_data():
    return rep.get_top_sales_count()

@app.post('/api/chatbot')
def chatbot(request: ChatRequest):
    return gpt_agent.process('user','user',request.input,context=rep.get_top_customers_csv_as_text()+rep.get_top_products_csv_text())

@app.post('/api/sqlbot')
def sqlbot(request: ChatRequest):
    return sql_agent.process('user','user',request.input, context=rep.sql_schema)
#endregion

#region: Assistants
def reset_assistant() -> AssistantAgent:
    
    store.delete('assistant','id')
    try:
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

@app.delete('/api/assistant/reset')
def delete_state():    
    reset_assistant()
    return {"status":"assistant reset"}

@app.post('/api/assistants')
def chatbot(request: ChatRequest):    
    return get_assistant_agent().process(request.user_name,request.user_id,request.input)

@app.get("/api/assistant/id")
def get_assistant_id():
    val = store.get('assistant','id')
    return {"assistant_id":val or "None"}
#endregion

#region: multiagent
bot_agent = GPTAgent(settings, client)
bot_agent.get_context_delegate = lambda: rep.get_top_customers_csv_as_text() + rep.get_top_products_csv_text()

sql_agent = SQLAgent(settings, client)
sql_agent.get_context_delegate = lambda: rep.sql_schema

bot_agent_registration = AgentRegistration(settings, client, "SalesIntent", "Answer questions related to customers, orders and products.", bot_agent)
sql_bot_registration = AgentRegistration(settings, client, "SqlIntent", "Generate and process SQL statement.", sql_agent)
assistant_registration = AgentRegistration(settings, client, "AssistantIntent", "Generate chart, bars, and graphs related customes, orders, and products.", get_assistant_agent())

proxy = AgentProxy(settings, client, [bot_agent_registration, sql_bot_registration,assistant_registration])

@app.post('/api/multiagent')
def chatbot(request: ChatRequest):
    return proxy.process(request.user_name,request.user_id,request.input)
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