using Azure.AI.OpenAI;
using models;

namespace agents;

public class RAGAgent(AgentSettings? settings, OpenAIClient? client) : BaseAgent(settings, client)
{
    public override Task<List<ChatMessage>> ProcessAsync(string user_name, string user_id, string prompt, int max_tokens = 500, float temperature = 0.3f, string context = "")
    {
        throw new NotImplementedException();
    }
}