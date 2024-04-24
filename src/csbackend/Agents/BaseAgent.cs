using Azure;
using Azure.AI.OpenAI;
using models;

namespace agents;

public delegate string GetContentDelegate();

public abstract class BaseAgent : IAgent
{
    public AgentSettings Settings { get; set; } = null!;
    public OpenAIClient Client { get; set; } = null!;
    public GetContentDelegate? GetContent { get; set; }


    public BaseAgent(AgentSettings? settings, OpenAIClient? client, GetContentDelegate? getContent = null)
    {
        Settings = settings ?? new AgentSettings();
        Client = client ?? new OpenAIClient(new Uri(Settings.API_Endpoint), new AzureKeyCredential(Settings.API_Key));

        GetContent = getContent;
    }


    //ChatMessage(role='user',user_name=user_name,user_id=user_id,content=prompt,columns=[],rows=[]),
    public abstract Task<List<ChatMessage>> ProcessAsync(string user_name, string user_id, string prompt, int max_tokens = 500, float temperature = 0.3f, string context = "");
}