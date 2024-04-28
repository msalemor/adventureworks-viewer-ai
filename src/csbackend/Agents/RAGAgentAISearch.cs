using System.Reflection.Metadata;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using Azure.AI.OpenAI;
using models;

namespace agents;

public record AISearchResult(
    [property: JsonPropertyName("@search.score")] float SearchScore,
    [property: JsonPropertyName("@search.rerankerScore")] float RerankerScore,
    [property: JsonPropertyName("chunk_id")] string ChunkId,
    [property: JsonPropertyName("parent_id")] string ParentId,
    [property: JsonPropertyName("chunk")] string Chunk,
    [property: JsonPropertyName("title")] string Title
);

// var payload = new
//         {
//             search = input,
//             vectorQueries = new[]{
//                 new{
//                     text = input,
//                     kind = "text",
//                     k = limit,
//                     fields = "vector"
//                 }
//             },
//             semanticConfiguration = Settings.AISearch_Semantic_Configuration,
//             top = limit,
//             queryType = "semantic",
//             select = "chunk_id,parent_id,chunk,title",
//             queryLanguage = "en-US"
//         };
public record VectorQuery(
    [property: JsonPropertyName("text")] string Text,
    [property: JsonPropertyName("kind")] string Kind,
    [property: JsonPropertyName("k")] int K,
    [property: JsonPropertyName("fields")] string Fields
);
public record AISearchRequest(
    [property: JsonPropertyName("search")] string Search,
    [property: JsonPropertyName("vectorQueries")] VectorQuery[] VectorQueries,
    [property: JsonPropertyName("semanticConfiguration")] string SemanticConfiguration,
    [property: JsonPropertyName("top")] int Top,
    [property: JsonPropertyName("queryType")] string QueryType,
    [property: JsonPropertyName("select")] string Select,
    [property: JsonPropertyName("queryLanguage")] string QueryLanguage
);


public class RAGAgentAISearch(AgentSettings? settings, OpenAIClient? client) : BaseAgent(settings, client)
{
    public HttpClient HttpClient { get; set; } = null!;

    private async Task<List<AISearchResult>> CallAISearch(string input, int limit = 3)
    {
        var payload = new
        {
            search = input,
            vectorQueries = new[]{
                new{
                    text = input,
                    kind = "text",
                    k = limit,
                    fields = "vector"
                }
            },
            semanticConfiguration = Settings.AISearch_Semantic_Configuration,
            top = limit,
            queryType = "semantic",
            select = "chunk_id,parent_id,chunk,title",
            queryLanguage = "en-US"
        };
        var req = new HttpRequestMessage(HttpMethod.Post, Settings.AISearch_Endpoint);
        req.Headers.Add("api-key", Settings.AISearch_APIKey);
        req.Content = new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json");
        var res = await HttpClient.SendAsync(req);
        if (res.IsSuccessStatusCode)
        {
            var content = await res.Content.ReadAsStringAsync();
            var results = JsonSerializer.Deserialize<List<AISearchResult>>(content) ?? [];
            return results;
        }
        else
        {
            return [];
        }
    }

    public override async Task<List<ChatMessage>> ProcessAsync(string user_name, string user_id, string prompt, int max_tokens = 500, float temperature = 0.3f, string context = "")
    {
        var results = await CallAISearch(prompt);
        var chunkContext = new StringBuilder();
        foreach (var result in results)
        {
            chunkContext.AppendLine(result.Chunk);
        }

        string fullPrompt = $"user:\n{prompt}\nText: \"\"\"\n{chunkContext}\n\"\"\"";
        var completion = await AgentUtils.CallGPTAsync(Client, Settings.GPT_Model_Deployment_Name, fullPrompt, temperature);
        if (completion is not null)
        {
            var outputMessages = new List<ChatMessage>
                {
                    new("user", user_name, user_id, prompt, [], []),
                    new("assistant", user_name, user_id, completion, [],[])
                };
            return outputMessages;
        }
        else
        {
            return [];
        }
    }
}

