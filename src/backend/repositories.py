import os
import pymssql
import dotenv

dotenv.load_dotenv()

DB_SERVER = os.getenv('DB_SERVER')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_DATABASE = os.getenv('DB_DATABASE')

if DB_SERVER is None or DB_USER is None or DB_PASSWORD is None or DB_DATABASE is None:
    raise ValueError("Missing environment variables DB_SERVER, DB_USER, DB_PASSWORD, DB_DATABASE")

conn = pymssql.connect(
    server=DB_SERVER,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_DATABASE,
    as_dict=True    
)  

sql_schema = """
Tables
vCustomer: A table of customers.
vProductAndDescription: A table of products with their description.
vOrderDetails: A table of order details by CustomerID and ProductID. This list does not container the customer last or fist name.
vTopProductsSold: A table of the top products sold.
vTopSales: A table of customers and their purchase totals.

SELECT TOP (1000) [CustomerID]
      ,[LastName]
      ,[FirstName]
      ,[EmailAddress]
      ,[SalesPerson]
      ,[City]
      ,[StateProvince]
      ,[CountryRegion]
      ,[Orders]
      ,[TotalDue]
  FROM [SalesLT].[vCustomers]

SELECT TOP (1000) [ProductID]
      ,[Name]
      ,[ProductModel]
      ,[Culture]
      ,[Description]
  FROM [SalesLT].[vProductAndDescription]


SELECT TOP (1000) [CustomerID]
      ,[SalesOrderID]
      ,[ProductID]
      ,[Category]
      ,[Model]
      ,[Description]
      ,[OrderQty]
      ,[UnitPrice]
      ,[UnitPriceDiscount]
      ,[LineTotal]
  FROM [SalesLT].[vOrderDetails]

SELECT TOP (1000) [ProductId]
      ,[category]
      ,[model]
      ,[description]
      ,[TotalQty]
  FROM [SalesLT].[vTopProductsSold]

SELECT TOP (1000) [CustomerID]
      ,[LastName]
      ,[FirstName]
      ,[EmailAddress]
      ,[SalesPerson]
      ,[Total]
      ,[City]
      ,[StateProvince]
      ,[CountryRegion]
  FROM [SalesLT].[vTopSales]
"""


def get_customers():
    cursor = conn.cursor()
    sql_cmd = """select * from SalesLT.vCustomers
order by LastName,FirstName"""
    cursor.execute(sql_cmd)
    columns = [{'key':column[0],'name':column[0],'resizable':True} for column in cursor.description]
    rows = cursor.fetchall()
    return {'columns':columns,'rows':rows}    

def get_customer_count() -> int:
    cursor = conn.cursor()
    sql_cmd = """select count(*) as count from SalesLT.vCustomers"""
    cursor.execute(sql_cmd)
    row = cursor.fetchone()
    return row['count']

def get_top_customers():
    cursor = conn.cursor()
    sql_cmd = """select CustomerID,LastName,FirstName,EmailAddress,SalesPerson,City,StateProvince,CountryRegion,Total 
from [SalesLT].[vTopCustomers]
order by total desc"""
    cursor.execute(sql_cmd)
    columns = [{'key':column[0],'name':column[0],'resizable':True} for column in cursor.description]
    rows = cursor.fetchall()        
    return {'columns':columns,'rows':rows}

def get_top_customers_count() -> int:
    cursor = conn.cursor()
    sql_cmd = """select count(*) as count from [SalesLT].[vTopCustomers]"""
    cursor.execute(sql_cmd)
    row = cursor.fetchone()
    return row['count']

def get_top_customers_csv_as_text():
    colsandrows =get_top_customers()    
    rows = colsandrows['rows']
    columns = colsandrows['columns']
    text = "Customer data\n"
    #text += "CustomerID,LastName,FirstName,EmailAddress,SalesPerson,City,StateProvince,CountryRegion,Total\n"
    text += ",".join([column['key'] for column in columns]) + "\n"
    for row in rows:
        text += f"{row['CustomerID']},{row['LastName']},{row['FirstName']},{row['EmailAddress']},{row['SalesPerson']},{row['City']},{row['StateProvince']},{row['CountryRegion']},{row['Total']}\n"
    return text

def get_products():
    cursor = conn.cursor()
    sql_cmd = """select ProductId,Name,ProductModel,[Description] from [SalesLT].[vProductAndDescription]
where culture='en' order by description"""
    cursor.execute(sql_cmd)
    columns = [{'key':column[0],'name':column[0],'resizable':True} for column in cursor.description]
    rows = cursor.fetchall()        
    return {'columns':columns,'rows':rows}   

def get_products_count() -> int:
    cursor = conn.cursor()
    sql_cmd = """select count(*) as count from [SalesLT].[vProductAndDescription]
where culture='en'"""
    cursor.execute(sql_cmd)
    row = cursor.fetchone()    
    return row['count']

def get_top_products():
    cursor = conn.cursor()
    sql_cmd = """select * from [SalesLT].[vTopProductsSold] order by TotalQty desc"""
    cursor.execute(sql_cmd)
    columns = [{'key':column[0],'name':column[0],'resizable':True} for column in cursor.description]
    rows = cursor.fetchall()    
    return {'columns':columns,'rows':rows}

def get_top_products_csv_text():
    colsandrows = get_top_products()
    columns = colsandrows['columns']
    rows = colsandrows['rows']
    text = "Product data\n"    
    text += ",".join([column['key'] for column in columns]) + "\n"
    for row in rows:
        text += f"{row['ProductId']},{row['category']},{row['model']},{row['description']},{row['TotalQty']}\n"
    return text

def get_top_products_count() -> int:
    cursor = conn.cursor()
    sql_cmd = """select count(*) as count from [SalesLT].[vTopProductsSold]"""
    cursor.execute(sql_cmd)
    row = cursor.fetchone()
    return row['count']

def get_order_details():
    cursor = conn.cursor()
    sql_cmd = """select * from [SalesLT].[vOrderDetails] order by OrderQty desc"""
    cursor.execute(sql_cmd)
    columns = [{'key':column[0],'name':column[0],'resizable':True} for column in cursor.description]
    rows = cursor.fetchall()    
    return {'columns':columns,'rows':rows}

def get_order_details():
    cursor = conn.cursor()
    sql_cmd = """select * from [SalesLT].[vOrderDetails]"""
    cursor.execute(sql_cmd)
    rows = cursor.fetchall()    
    columns = [{'key':column[0],'name':column[0],'resizable':True} for column in cursor.description]
    return {'columns':columns,'rows':rows}

def get_order_details_count():
    cursor = conn.cursor()
    sql_cmd = """select count(*) as count from [SalesLT].[vOrderDetails]"""
    cursor.execute(sql_cmd)
    row = cursor.fetchone()
    return row['count']

def get_all_counts():
    results = {
        'customers':get_customer_count(),
        'topCustomers':get_top_customers_count(),
        'products':get_products_count(),
        'topProducts':get_top_products_count(),
        'orderDetails':get_order_details_count(),        
    }
    return results

def export_top_customers_csv():
    rowsancols = get_top_customers()
    rows = rowsancols['rows']
    with open('wwwroot/assets/data/top_customers.csv', 'w') as f:
        f.write("CustomerID,LastName,FirstName,EmailAddress,SalesPerson,City,StateProvince,CountryRegion,Total\n")
        for row in rows:
            f.write(f"{row['CustomerID']},{row['LastName']},{row['FirstName']},{row['EmailAddress']},{row['SalesPerson']},{row['City']},{row['StateProvince']},{row['CountryRegion']},{row['Total']}\n")

def export_top_products_csv():
    rowsancols = get_top_products()
    rows = rowsancols['rows']
    with open('wwwroot/assets/data/top_products.csv', 'w') as f:
        f.write("ProductId,category,model,description,TotalQty\n")
        for row in rows:
            f.write(f"{row['ProductId']},{row['category']},{row['model']},{row['description']},{row['TotalQty']}\n")

def sql_executor(sql_cmd:str) -> dict:
    try:
        cursor = conn.cursor()    
        cursor.execute(sql_cmd)
        rows = cursor.fetchall()    
        columns = [{'key':column[0],'name':column[0],'resizable':True} for column in cursor.description]
        return {'columns':columns,'rows':rows}
    except:
        return {'columns':[],'rows':[]}
    