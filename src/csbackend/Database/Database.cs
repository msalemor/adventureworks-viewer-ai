using System.Data;
using Microsoft.Data.SqlClient;
using Microsoft.VisualBasic;

namespace Database;

public class DatabaseUtil
{
    public const string sql_schema = @"Tables
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
  FROM [SalesLT].[vTopCustomers]

Sample queries:
Q: What customers are in the United States?
A: SELECT * FROM [SalesLT].[vCustomers] WHERE [CountryRegion] = 'United States'
Q: In what countries are there customers who have bought products?
A: SELECT DISTINCT vCustomers.CountryRegion FROM SalesLT.vCustomers INNER JOIN SalesLT.vOrderDetails ON vCustomers.CustomerID = vOrderDetails.CustomerID
";

    public string CONNECTION_STRING { get; set; } = null!;
    private SqlConnection GetConnection() => new(CONNECTION_STRING);

    public async Task<int> CanConnect()
    {
        try
        {
            var conn = GetConnection();
            await conn.OpenAsync();
            var result = conn.State == ConnectionState.Open;
            conn.Close();
            return result ? 1 : 0;
        }
        catch
        {
            return 0;
        }
    }

    // def get_customers():
    //     logger.info("Getting customers")
    //     cursor = conn.cursor()
    //     sql_cmd = """select * from SalesLT.vCustomers
    // order by LastName,FirstName"""
    //     cursor.execute(sql_cmd)
    //     columns = [{'key':column[0],'name':column[0],'resizable':True} for column in cursor.description]
    //     rows = cursor.fetchall()
    //     return {'columns':columns,'rows':rows}  

    private async Task<Tuple<List<object>, List<object>>> GetRowsAndCols(string sqlCmd)
    {
        var conn = GetConnection();
        await conn.OpenAsync();
        //var sql_cmd = "select * from SalesLT.vCustomers order by LastName,FirstName";
        using var cmd = conn.CreateCommand();
        cmd.CommandText = sqlCmd;

        using var reader = await cmd.ExecuteReaderAsync();
        var columns = new List<object>();
        for (int i = 0; i < reader.FieldCount; i++)
        {
            columns.Add(new { key = reader.GetName(i), name = reader.GetName(i), resizable = true });
        }

        var rows = new List<object>();
        while (await reader.ReadAsync())
        {
            var row = new Dictionary<string, object?>();
            for (int i = 0; i < reader.FieldCount; i++)
            {
                row[reader.GetName(i)] = reader.GetValue(i) == DBNull.Value ? null : reader.GetValue(i);
            }
            rows.Add(row);
        }

        return new Tuple<List<object>, List<object>>(columns, rows);
    }


    private async Task<int> GetCount(string sqlCmd)
    {
        var conn = GetConnection();
        await conn.OpenAsync();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = sqlCmd;
        int count = (int)(await cmd.ExecuteScalarAsync() ?? 0);
        return count;
    }

    public async Task<Tuple<List<object>, List<object>>> GetCustomers()
    {
        return await GetRowsAndCols("select * from SalesLT.vCustomers order by LastName,FirstName");
    }
    public async Task<int> GetCustomerCount()
    {
        return await GetCount("select count(*) from SalesLT.vCustomers");
    }
    public async Task<Tuple<List<object>, List<object>>> GetTopCustomers()
    {
        return await GetRowsAndCols(@"CustomerID,LastName,FirstName,EmailAddress,SalesPerson,
City,StateProvince,CountryRegion,Total from [SalesLT].[vTopCustomers] order by Total desc");
    }

    public async Task<int> GetTopCustomersCount()
    {
        return await GetCount("select count(*) from SalesLT.vTopCustomers");
    }

    public async Task<Tuple<List<object>, List<object>>> GetProducs()
    {
        return await GetRowsAndCols("select * from SalesLT.vProductAndDescription where culture='en'");
    }

    public async Task<int> GetProductsCount()
    {
        return await GetCount("select count(*) from SalesLT.vProductAndDescription");
    }

    public async Task<Tuple<List<object>, List<object>>> GetTopProducs()
    {
        return await GetRowsAndCols("select * from SalesLT.vTopProductsSold order by TotalQty desc");
    }
    public async Task<int> GetTopProductsCount()
    {
        return await GetCount("select count(*) from SalesLT.vTopProductsSold");
    }

    public async Task<Tuple<List<object>, List<object>>> GetOrderDetails()
    {
        return await GetRowsAndCols("select * from SalesLT.vOrderDetails order by CustomerID,ProductID");
    }
    public async Task<int> GetOrderDetailsCount()
    {
        return await GetCount("select count(*) from SalesLT.vOrderDetails");
    }

}