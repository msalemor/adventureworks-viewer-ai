using Azure;
using Azure.AI.OpenAI;
using Database;
using models;

namespace agents;

public class SQLAgent(AgentSettings? settings, OpenAIClient? client) : BaseAgent(settings, client)
{
    public override async Task<List<ChatMessage>> ProcessAsync(string user_name, string user_id, string prompt, int max_tokens = 500, float temperature = 0.3f, string context = "")
    {
        if (GetContent is not null)
        {
            context += GetContent();
        }

        try
        {
            ChatCompletionsOptions chatCompletionsOptions = new()
            {
                DeploymentName = Settings.GPT_Model_Deployment_Name, // Use DeploymentName for "model" with non-Azure clients
                Messages =
                {
                    new ChatRequestSystemMessage("You are an agent that can help generate sql statements based on the schema provided. Here is the schema:\n" + context),
                    new ChatRequestUserMessage($"Generate the best SQL statement for:\n{prompt}\nOutput the SQL statement ONLY."),
                },
                Temperature = temperature,
                MaxTokens = max_tokens
            };

            Response<ChatCompletions> response = await Client.GetChatCompletionsAsync(chatCompletionsOptions);
            ChatResponseMessage chatResponseMessage = response.Value.Choices[0].Message;
            string sql_statement = chatResponseMessage.Content;


            sql_statement = sql_statement.Replace("```", "")
            .Replace("\n", " ")
            .Replace("sql", "")
            .Replace(";", "");

            return
            [
                new("user", user_name, user_id, prompt, [], []),
                new("assistant", user_name, user_id, sql_statement, [], [])
            ];

        }
        catch (Exception e)
        {
            Console.WriteLine(e.ToString());
            return [];
        }
    }
}