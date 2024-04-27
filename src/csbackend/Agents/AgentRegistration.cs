namespace agents;

using Azure.AI.OpenAI;

public class AgentRegistration
{
    //public AgentSettings Settings { get; set; } = null!;
    public OpenAIClient Client { get; set; } = null!;
    public IAgent Agent { get; set; } = null!;
    public string Intent { get; set; } = null!;
    public string IntentDesc { get; set; } = null!;

    public AgentRegistration(string intent, string intentDesc, IAgent agent, AgentSettings? settings = null)
    {
        Agent = agent;
        Intent = intent;
        IntentDesc = intentDesc;
    }
}