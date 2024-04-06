import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from openai import AzureOpenAI
from kcvstore import KCVStore
from AgentSettings import AgentSettings
from AssistantAgent import AssistantAgent
from GPTAgent import GPTAgent
from SQLAgent import SQLAgent
import repositories as rep
from AgentRegistration import AgentRegistration
from AgentProxy import AgentProxy
from Models import ChatRequest


import dotenv
dotenv.load_dotenv()

openapi_url = os.getenv("OPENAPI_URL")
app = FastAPI(openapi_url=openapi_url, title="AdventureWorks API", version="0.1.0")

#logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = AgentSettings()
client = AzureOpenAI(azure_endpoint=settings.api_endpoint, api_key=settings.api_key, api_version=settings.api_version)
gpt_agent = GPTAgent(settings, client)
sql_agent = SQLAgent(settings, client)
store = KCVStore('settings.db')

logger.info("Creating top customers csv file")
rep.export_top_customers_csv()
logger.info("Creating top products csv file")
rep.export_top_products_csv()


#region: CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#endregion

#region: API
@app.post("/api/reindex")
def reindex():
    rep.export_top_customers_csv()
    rep.export_top_products_csv()
    logging.info("reindexed the csv files")
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
assistant_agent : AssistantAgent= None
def reset_assistant():
    
    store.delete('assistant','id')
    try:
        assistant_agent.cleanup()
    except:
        pass

    assistant_agent = AssistantAgent(settings, client, 
                                    "AdventureWorks Assistant",
                                    "You are a friendly asssitant that can help answer questions about customers, orders and products using the provided information.",
                                    "wwwroot/assets/data/",
                                    [{"type": "code_interpreter"}])
    store.set('assistant','id',assistant_agent.assistant.id)

    return {'status':f'assistant created {assistant_agent.assistant.id}'}

val = store.get('assistant','id')
if val:
    agent = client.beta.assistants.retrieve(val)
    assistant_agent = AssistantAgent(settings, client, "", "", "", tools_list=[], assistant=agent)
    logger.info(f"Reloaded assistant {assistant_agent.assistant.id}")
else:
    reset_assistant()

@app.delete('/api/assistant')
def delete_state():    
    return reset_assistant()

@app.post('/api/assistants')
def chatbot(request: ChatRequest):
    return assistant_agent.process_prompt(request.user_name,request.user_id,request.input)
#endregion

#region: multiagent
bot_agent = GPTAgent(settings, client)
bot_agent.get_context_delegate = lambda: rep.get_top_customers_csv_as_text() + rep.get_top_products_csv_text()

sql_agent = SQLAgent(settings, client)
sql_agent.get_context_delegate = lambda: rep.sql_schema

bot_agent_registration = AgentRegistration(settings, client, "SalesIntent", "Answer questions related to customers, orders and products.", bot_agent)
sql_bot_registration = AgentRegistration(settings, client, "SqlIntent", "Generate and process SQL statement.", sql_agent)
assistant_registration = AgentRegistration(settings, client, "AssistantIntent", "Generate chart, bars, and graphs related customes, orders, and products.", assistant_agent)

proxy = AgentProxy(settings, client, [bot_agent_registration, sql_bot_registration,assistant_registration])

@app.post('/api/multiagent')
def chatbot(request: ChatRequest):
    return proxy.process(request.user_name,request.user_id,request.input)
#endregion


#region: Static Files
app.mount("/", StaticFiles(directory="wwwroot",html = True), name="static")
#endregion
