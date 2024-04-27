using agents;
using Azure;
using Azure.AI.OpenAI;
using Azure.AI.OpenAI.Assistants;
using Database;
using dotenv.net;
using models;

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
KCVStore kcv = new("Data Source=./cssettings.db;");
builder.Services.AddSingleton(kcv);

// Get the connection string from the environment variables
var connStr = Environment.GetEnvironmentVariable("CONN_STR") ?? "";
if (string.IsNullOrEmpty(connStr))
{
    Console.WriteLine("Database connection string is empty and is required.");
    Environment.Exit(1);
}
// Create a new instance of the DatabaseUtil class
DatabaseUtil db = new()
{
    CONNECTION_STRING = connStr,
};
// Add the DatabaseUtil instance to the service container
builder.Services.AddSingleton(db);

AgentSettings settings = new();
OpenAIClient client = new(new Uri(settings.API_Endpoint), new AzureKeyCredential(settings.API_Key));
AssistantsClient asstClient = new(new Uri(settings.API_Endpoint), new AzureKeyCredential(settings.API_Key));

GPTAgent gptAgent = new(settings, client);
SQLAgent sqlAgent = new(settings, client, db);


async Task<AssistantsAPIAgent> LoadOrCreateAssistant()
{
    AssistantsAPIAgent asstAgent;
    var assistantID = await kcv.Get("assistant", "id");
    try
    {
        if (string.IsNullOrEmpty(assistantID))
        {
            throw new RequestFailedException("Assistant ID not found in KCV store.");
        }
        asstAgent = new(settings, asstClient, kcv)
        {
            Assistant = await asstClient.GetAssistantAsync(assistantID)
        };
    }
    catch (Exception)
    {
        asstAgent = new AssistantsAPIAgent(settings, asstClient, kcv);
        await asstAgent.CreateAssistantAsync("Sales Assistant", "You are a friendly assistant that can generate general math related chart and graphs and bars and charts related to customers, products or orders.", [], null, false);
    }
    return asstAgent;
}
var asstAgent = await LoadOrCreateAssistant();

AgentRegistration gptAgentRegistration = new("SalesIntent", "Answer questions related to customers, orders and products.", gptAgent, settings);
AgentRegistration sqlAgentRegistration = new("SqlIntent", "Generate and process SQL statement.", sqlAgent, settings);
AgentRegistration asstAgentRegistration = new("AssistantIntent", "Generate chart or graphs related to customers, orders and products.", asstAgent, settings);
ProxyAgent proxyAgent = new([gptAgentRegistration, sqlAgentRegistration, asstAgentRegistration], settings, client);

var topCustomersCSV = db.GetTopProductsCSV();
var topProductsCSV = db.GetTopCustomerCSV();

builder.Services.AddSingleton(gptAgent);
builder.Services.AddSingleton(sqlAgent);
builder.Services.AddSingleton(proxyAgent);

var app = builder.Build();

// Configure the HTTP request pipeline.
//if (app.Environment.IsDevelopment())
//{
app.UseSwagger();
app.UseSwaggerUI();
//}
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
var group = app.MapGroup("/api");

group.MapGet("/reindex", (DatabaseUtil db) =>
{
    var status = new { Status = "OK" };
    return Results.Ok(status);
})
.WithName("Reindex")
.WithOpenApi();

group.MapGet("/status", () =>
{
    var status = new { Status = "OK" };
    return Results.Ok(status);
})
.WithName("Status")
.WithOpenApi();

// @app.get("/api/counts")
// def read_data():
//     return rep.get_all_counts()
group.MapGet("/counts", async (DatabaseUtil db) =>
{
    var counts = new
    {
        customers = await db.GetCustomerCount(),
        topCustomers = await db.GetTopCustomersCount(),
        products = await db.GetProductsCount(),
        topProducts = await db.GetTopProductsCount(),
        orderDetails = await db.GetOrderDetailsCount()
    };
    return Results.Ok(counts);
})
.WithName("count")
.WithOpenApi();

// @app.get("/api/customers")
// def read_data():
//     return rep.get_customers()
group.MapGet("/customers", async (DatabaseUtil db) =>
{
    var (columns, rows) = await db.GetCustomers();
    return new { columns, rows };
})
.WithName("customers")
.WithOpenApi();

// @app.get("/api/customers/top")
// def read_data():
//     return rep.get_top_customers()
group.MapGet("/customers/top", async (DatabaseUtil db) =>
{
    var (columns, rows) = await db.GetTopCustomers();
    return new { columns, rows };
})
.WithName("topcustomers")
.WithOpenApi();

// @app.get("/api/products")
// def read_data():
//     return rep.get_products()
group.MapGet("/products", async (DatabaseUtil db) =>
{
    var (columns, rows) = await db.GetProducs();
    return new { columns, rows };
})
.WithName("products")
.WithOpenApi();
// @app.get("/api/products/sold")
// def read_data():
//     return rep.get_top_products()
group.MapGet("/products/top", async (DatabaseUtil db) =>
{
    var (columns, rows) = await db.GetTopProducs();
    return new { columns, rows };
})
.WithName("topProducts")
.WithOpenApi();

// @app.get("/api/orders")
// def read_data():
//     return rep.get_order_details()
group.MapGet("/orders", async (DatabaseUtil db) =>
{
    var (columns, rows) = await db.GetOrderDetails();
    return new { columns, rows };
})
.WithName("orders")
.WithOpenApi();

group.MapPost("/chatbot", async (ChatRequest request, GPTAgent gptAgent) =>
{
    return await gptAgent.ProcessAsync("user", "user", request.input, request.max_tokens, request.temperature, topCustomersCSV + topProductsCSV);
})
.WithName("chatbot")
.WithOpenApi();

group.MapPost("/sqlbot", async (ChatRequest request, SQLAgent sqlAgent) =>
{
    return await sqlAgent.ProcessAsync("user", "user", request.input, request.max_tokens, request.temperature, DatabaseUtil.sql_schema);
})
.WithName("sqlbot")
.WithOpenApi();

group.MapPost("/rag", async (ChatRequest request, SQLAgent sqlAgent) =>
{
    return await gptAgent.ProcessAsync("user", "user", request.input, request.max_tokens, request.temperature, DatabaseUtil.sql_schema);
})
.WithName("rag")
.WithOpenApi();

group.MapPost("/assistants", async (ChatRequest request, SQLAgent sqlAgent) =>
{
    return await asstAgent.ProcessAsync("user", "user", request.input, request.max_tokens, request.temperature, DatabaseUtil.sql_schema);
})
.WithName("assistants")
.WithOpenApi();

group.MapDelete("/assistant/reset", async () =>
{
    var oldId = "";
    var newId = "";
    try
    {
        oldId = await kcv.Get("assistant", "id");
        asstAgent.Assistant = await asstClient.GetAssistantAsync(oldId);
        await asstAgent.CleanupAsync();
    }
    finally
    {
        await kcv.Delete("assistant", "id");
    }
    asstAgent = await LoadOrCreateAssistant();
    newId = asstAgent.Assistant.Id;
    if (oldId != newId)
    {
        return Results.Ok(new { message = $"Assistant reset successful. Old id: {oldId} - New id: {newId}" });
    }

    return Results.BadRequest(new { message = $"Assistant reset failed for: {oldId}" });
})
.WithName("assistants_reset")
.WithOpenApi();

group.MapPost("/multiagent", async (ChatRequest request, ProxyAgent proxyAgent) =>
{
    return await proxyAgent.ProcessAsync("user", "user", request.input);
})
.WithName("multiagent")
.WithOpenApi();

#endregion

#region: App & Static Files

app.UseStaticFiles();
app.MapFallbackToFile("index.html");
app.Run();

#endregion


