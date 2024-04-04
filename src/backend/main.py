from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from openai import AzureOpenAI
from AgentSettings import AgentSettings
from GPTAgent import GPTAgent

import repositories as rep

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/reindex")
def reindex():
    rep.export_products_as_csv()
    rep.export_customers_as_csv()
    rep.export_top_products_sold_as_csv()
    rep.export_top_sales_as_csv()
    rep.export_order_details_as_csv()
    return {"status": "reindex"}

@app.get("/api/customers")
def read_data():
    return rep.get_customers()

@app.get("/api/customers/count")
def read_data():
    return {'count':rep.get_customer_count()}

@app.get("/api/customers/top")
def read_data():
    return rep.get_top_customers()

@app.get("/api/customers/top/count")
def read_data():
    return rep.get_top_customers_count()

@app.get("/api/products")
def read_data():
    return rep.get_products()

@app.get("/api/products/count")
def read_data():
    return rep.get_products_count()

@app.get("/api/products/sold")
def read_data():
    return rep.get_top_products()

@app.get("/api/products/sold/count")
def read_data():
    return rep.get_top_products_count()

@app.get("/api/orders")
def read_data():
    return rep.get_order_details()

@app.get("/api/orders/count")
def read_data():
    return rep.get_order_details_count()

@app.get("/api/counts")
def read_data():
    return rep.get_all_counts()

@app.get("/api/sales/count")
def read_data():
    return rep.get_top_sales_count()

settings = AgentSettings()
client = AzureOpenAI(azure_endpoint=settings.api_endpoint, api_key=settings.api_key, api_version=settings.api_version)
agent = GPTAgent(settings, client)

class ChatRequest(BaseModel):
    user_name:str = 'user'
    user_id: str = 'user'
    input: str
    max_tokens: int = 500
    temperature: float = 0.3

@app.post('/api/chatbot')
def chatbot(request: ChatRequest):
    return agent.process_prompt('user','user',request.input,context=rep.get_top_customers_csv_as_text()+rep.get_top_products_csv_text())

@app.post('/api/sqlbot')
def chatbot(request: ChatRequest):
    return agent.process_sql('user','user',request.input, schema=rep.sql_schema)

app.mount("/", StaticFiles(directory="wwwroot"), name="static")

# @app.get("/items/{item_id}")
# def read_item(item_id: int, q: Union[str, None] = None):
#     return {"item_id": item_id, "q": q}
