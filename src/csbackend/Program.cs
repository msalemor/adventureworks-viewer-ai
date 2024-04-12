using Database;
using dotenv.net;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
// Learn more about configuring Swagger/OpenAPI at https://aka.ms/aspnetcore/swashbuckle
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();
builder.Services.AddCors(policy =>
{
    policy.AddDefaultPolicy(builder =>
    {
        builder.AllowAnyOrigin()
            .AllowAnyMethod()
            .AllowAnyHeader();
    });
});
DotEnv.Load();
var connStr = Environment.GetEnvironmentVariable("CONN_STR") ?? "";
if (string.IsNullOrEmpty(connStr))
{
    Console.WriteLine("The environment variable CONN_STR is missing.");
    Environment.Exit(1);
}
DatabaseUtil db = new()
{
    CONNECTION_STRING = connStr
};
builder.Services.AddSingleton(db);

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}
app.UseCors();

// var summaries = new[]
// {
//     "Freezing", "Bracing", "Chilly", "Cool", "Mild", "Warm", "Balmy", "Hot", "Sweltering", "Scorching"
// };

// app.MapGet("/weatherforecast", () =>
// {
//     var forecast = Enumerable.Range(1, 5).Select(index =>
//         new WeatherForecast
//         (
//             DateOnly.FromDateTime(DateTime.Now.AddDays(index)),
//             Random.Shared.Next(-20, 55),
//             summaries[Random.Shared.Next(summaries.Length)]
//         ))
//         .ToArray();
//     return forecast;
// })
// .WithName("GetWeatherForecast")
// .WithOpenApi();

#region APIs
var group = app.MapGroup("/api/v1");

group.MapGet("/api/reindex", (DatabaseUtil db) =>
{
    var status = new { Status = "OK" };
    return Results.Ok(status);
})
.WithName("Reindex")
.WithOpenApi();

group.MapGet("/api/status", () =>
{
    var status = new { Status = "OK" };
    return Results.Ok(status);
})
.WithName("Status")
.WithOpenApi();

// @app.get("/api/counts")
// def read_data():
//     return rep.get_all_counts()
group.MapGet("/api/counts", async (DatabaseUtil db) =>
{
    var counts = new
    {
        customers = await db.GetCustomerCount(),
        topcustomers = await db.GetTopCustomersCount(),
        products = await db.GetProductsCount(),
        topProducts = await db.GetTopProductsCount(),
        orders = await db.GetOrderDetailsCount()
    };
    return Results.Ok(counts);
})
.WithName("count")
.WithOpenApi();

// @app.get("/api/customers")
// def read_data():
//     return rep.get_customers()
group.MapGet("/api/customers", async (DatabaseUtil db) =>
{
    var (columns, rows) = await db.GetCustomers();
    return new { columns, rows };
})
.WithName("customers")
.WithOpenApi();

// @app.get("/api/customers/top")
// def read_data():
//     return rep.get_top_customers()
group.MapGet("/api/customers/top", async (DatabaseUtil db) =>
{
    var (columns, rows) = await db.GetTopCustomers();
    return new { columns, rows };
})
.WithName("topcustomers")
.WithOpenApi();

// @app.get("/api/products")
// def read_data():
//     return rep.get_products()
group.MapGet("/api/products", async (DatabaseUtil db) =>
{
    var (columns, rows) = await db.GetProducs();
    return new { columns, rows };
})
.WithName("products")
.WithOpenApi();
// @app.get("/api/products/sold")
// def read_data():
//     return rep.get_top_products()
group.MapGet("/api/products/sold", async (DatabaseUtil db) =>
{
    var (columns, rows) = await db.GetTopProducs();
    return new { columns, rows };
})
.WithName("topProducts")
.WithOpenApi();

// @app.get("/api/orders")
// def read_data():
//     return rep.get_order_details()
group.MapGet("/api/orders", async (DatabaseUtil db) =>
{
    var (columns, rows) = await db.GetOrderDetails();
    return new { columns, rows };
})
.WithName("orders")
.WithOpenApi();
// @app.get("/api/sales/count")
// def read_data():
//     return rep.get_top_sales_count()
// group.MapGet("/api/sales/count", async () =>
// {
//     var count = await DatabaseUtil.GetOrderDetailsCount();
//     return new { count };
// })
// .WithName("ordersCount")
// .WithOpenApi();

// @app.post('/api/chatbot')
// def chatbot(request: ChatRequest):
//     return gpt_agent.process('user','user',request.input,context=rep.get_top_customers_csv_as_text()+rep.get_top_products_csv_text())

// @app.post('/api/sqlbot')
// def sqlbot(request: ChatRequest):
//     return sql_agent.process('user','user',request.input, context=rep.sql_schema)


#endregion

#region: App & Static Files

app.Run();
app.UseStaticFiles();
app.UseDefaultFiles("index.html");

#endregion

// record WeatherForecast(DateOnly Date, int TemperatureC, string? Summary)
// {
//     public int TemperatureF => 32 + (int)(TemperatureC / 0.5556);
// }
