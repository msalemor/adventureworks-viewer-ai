using Azure.AI.OpenAI;
using models;

namespace agents;

public class GPTAgent(AgentSettings? settings, OpenAIClient? client) : BaseAgent(settings, client)
{
    public override async Task<List<ChatMessage>> ProcessAsync(string user_name, string user_id, string prompt, int max_tokens = 500, float temperature = 0.3f, string context = "")
    {
        if (GetContent is not null)
        {
            context += GetContent();
        }

        var fullPrompt = $"{prompt}\nText: \"\"\"\n{context}\n\"\"\"";
        var completion = await AgentUtils.CallGPTAsync(Client, Settings.GPT_Model_Deployment_Name, fullPrompt, temperature, max_tokens);
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