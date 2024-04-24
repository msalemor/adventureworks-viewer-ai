namespace agents;

using Azure;
using Azure.AI.OpenAI;

public class AgentRegistration
{
    public AgentSettings Settings { get; set; } = null!;
    public OpenAIClient Client { get; set; } = null!;
    public BaseAgent Agent { get; set; } = null!;
    public string Intent { get; set; } = null!;
    public string IntentDesc { get; set; } = null!;

    public AgentRegistration(string intent, string intentDesc, BaseAgent agent, AgentSettings? settings = null, OpenAIClient? client = null)
    {
        if (settings == null)
        {
            Settings = new AgentSettings();
        }

        if (client == null)
        {
            Client = new OpenAIClient(
                new Uri(settings!.API_Endpoint),
                new AzureKeyCredential(settings!.API_Key)
            );
        }

        Settings = settings!;
        Client = client!;
        Agent = agent;
        Intent = intent;
        IntentDesc = intentDesc;
    }
}