using System.Text.Json;
using Azure.AI.OpenAI.Assistants;

namespace agents;

public static class AgentSampleFunctions
{
    // Example of a function that defines no parameters
    public static string GetUserFavoriteCity() => "Seattle, WA";
    public static FunctionToolDefinition getUserFavoriteCityTool = new("getUserFavoriteCity", "Gets the user's favorite city.");
    // Example of a function with a single required parameter
    public static string GetCityNickname(string location) => location switch
    {
        "Seattle, WA" => "The Emerald City",
        "Los Angeles, CA" => "LA",
        "San Francisco, CA" => "The City by the Bay",
        "New York, NY" => "The Big Apple",
        "Chicago, IL" => "The Windy City",
        "Boston, MA" => "Beantown",
        "Miami, FL" => "The Magic City",
        "Austin, TX" => "The Live Music Capital of the World",
        "Portland, OR" => "The City of Roses",
        "Denver, CO" => "The Mile High City",
        "Las Vegas, NV" => "Sin City",
        "Nashville, TN" => "Music City",
        "New Orleans, LA" => "The Big Easy",
        _ => throw new NotImplementedException(),
    };
    public static FunctionToolDefinition getCityNicknameTool = new(
        name: "getCityNickname",
        description: "Gets the nickname of a city, e.g. 'LA' for 'Los Angeles, CA'.",
        parameters: BinaryData.FromObjectAsJson(
            new
            {
                Type = "object",
                Properties = new
                {
                    Location = new
                    {
                        Type = "string",
                        Description = "The city and state, e.g. San Francisco, CA",
                    },
                },
                Required = new[] { "location" },
            },
            new JsonSerializerOptions() { PropertyNamingPolicy = JsonNamingPolicy.CamelCase }));
    // Example of a function with one required and one optional, enum parameter
    public static string GetWeatherAtLocation(string location, string temperatureUnit = "f") => location switch
    {
        "Seattle, WA" => temperatureUnit == "f" ? "70f" : "21c",
        "Los Angeles, CA" => temperatureUnit == "f" ? "80f" : "27c",
        "San Francisco, CA" => temperatureUnit == "f" ? "65f" : "18c",
        "New York, NY" => temperatureUnit == "f" ? "75f" : "24c",
        "Chicago, IL" => temperatureUnit == "f" ? "70f" : "21c",
        "Boston, MA" => temperatureUnit == "f" ? "65f" : "18c",
        "Miami, FL" => temperatureUnit == "f" ? "85f" : "29c",
        "Austin, TX" => temperatureUnit == "f" ? "90f" : "32c",
        "Portland, OR" => temperatureUnit == "f" ? "60f" : "15c",
        "Denver, CO" => temperatureUnit == "f" ? "75f" : "24c",
        "Las Vegas, NV" => temperatureUnit == "f" ? "95f" : "35c",
        "Nashville, TN" => temperatureUnit == "f" ? "80f" : "27c",
        "New Orleans, LA" => temperatureUnit == "f" ? "85f" : "29c",
        _ => throw new NotImplementedException()
    };
    public static FunctionToolDefinition getCurrentWeatherAtLocationTool = new(
        name: "getCurrentWeatherAtLocation",
        description: "Gets the current weather at a provided location.",
        parameters: BinaryData.FromObjectAsJson(
            new
            {
                Type = "object",
                Properties = new
                {
                    Location = new
                    {
                        Type = "string",
                        Description = "The city and state, e.g. San Francisco, CA",
                    },
                    Unit = new
                    {
                        Type = "string",
                        Enum = new[] { "c", "f" },
                    },
                },
                Required = new[] { "location" },
            },
            new JsonSerializerOptions() { PropertyNamingPolicy = JsonNamingPolicy.CamelCase }));

    public static ToolOutput GetResolvedToolOutput(RequiredToolCall toolCall)
    {
        if (toolCall is RequiredFunctionToolCall functionToolCall)
        {
            if (functionToolCall.Name == getUserFavoriteCityTool.Name)
            {
                return new ToolOutput(toolCall, GetUserFavoriteCity());
            }
            using JsonDocument argumentsJson = JsonDocument.Parse(functionToolCall.Arguments);
            if (functionToolCall.Name == getCityNicknameTool.Name)
            {
                string locationArgument = argumentsJson.RootElement.GetProperty("location").GetString()!;
                return new ToolOutput(toolCall, GetCityNickname(locationArgument));
            }
            if (functionToolCall.Name == getCurrentWeatherAtLocationTool.Name)
            {
                string locationArgument = argumentsJson.RootElement.GetProperty("location").GetString()!;
                if (argumentsJson.RootElement.TryGetProperty("unit", out JsonElement unitElement))
                {
                    string unitArgument = unitElement.GetString()!;
                    return new ToolOutput(toolCall, GetWeatherAtLocation(locationArgument, unitArgument!));
                }
                return new ToolOutput(toolCall, GetWeatherAtLocation(locationArgument));
            }
        }
        return new ToolOutput(toolCall, "No tool was found for the provided tool call.");
    }

}
