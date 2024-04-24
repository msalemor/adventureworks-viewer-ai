using Azure;
using Azure.AI.OpenAI;
using models;

namespace agents;

public interface IAgent
{
    Task<List<ChatMessage>> ProcessAsync(string user_name, string user_id, string prompt, int max_tokens = 500, float temperature = 0.3f, string context = "");
}

//ChatMessage(role='user',user_name=user_name,user_id=user_id,content=prompt,columns=[],rows=[]),
//public record ChatMessage(string role, string content, string userName, string userId);


public static class AgentUtils
{
    internal static async Task<string?> CallGPTAsync(OpenAIClient client, string model_name, string prompt, float temperature = 0.1f, int max_tokens = 2)
    {
        try
        {
            ChatCompletionsOptions chatCompletionsOptions;
            if (max_tokens >= 0)
                chatCompletionsOptions = new ChatCompletionsOptions()
                {
                    DeploymentName = model_name, // Use DeploymentName for "model" with non-Azure clients
                    Messages =
                {
                    new ChatRequestUserMessage(prompt),
                },
                    Temperature = temperature,
                    MaxTokens = max_tokens
                };
            else
                chatCompletionsOptions = new ChatCompletionsOptions()
                {
                    DeploymentName = model_name, // Use DeploymentName for "model" with non-Azure clients
                    Messages =
                {
                    new ChatRequestUserMessage(prompt),
                },
                    Temperature = temperature
                };

            Response<ChatCompletions> response = await client.GetChatCompletionsAsync(chatCompletionsOptions);
            ChatResponseMessage responseMessage = response.Value.Choices[0].Message;

            return responseMessage.Content;
        }
        catch (Exception)
        {
            return null;
        }
    }
}