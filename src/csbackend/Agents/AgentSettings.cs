namespace agents;
using dotenv.net;

public class AgentSettings
{
    public string API_Endpoint { get; set; } = null!;
    public string API_Key { get; set; } = null!;
    public string API_Version { get; set; } = null!;
    public string GPT_Model_Deployment_Name { get; set; } = null!;
    public string ADA_Model_Deployment_Name { get; set; } = null!;
    //public string Email_URI { get; set; } = null!;
    public string AISearch_Endpoint { get; set; } = null!;
    public string AISearch_APIKey { get; set; } = null!;
    public string AISearch_Semantic_Configuration { get; set; } = null!;

    public AgentSettings()
    {
        DotEnv.Load();

        // Load environment variables
        API_Endpoint = Environment.GetEnvironmentVariable("OPENAI_URI") ?? string.Empty;
        API_Key = Environment.GetEnvironmentVariable("OPENAI_KEY") ?? string.Empty;
        API_Version = Environment.GetEnvironmentVariable("OPENAI_VERSION") ?? string.Empty;
        GPT_Model_Deployment_Name = Environment.GetEnvironmentVariable("OPENAI_GPT_DEPLOYMENT") ?? string.Empty;
        ADA_Model_Deployment_Name = Environment.GetEnvironmentVariable("OPENAI_ADA_DEPLOYMENT") ?? string.Empty;

        //Email_URI = Environment.GetEnvironmentVariable("EMAIL_URI") ?? string.Empty;
        AISearch_Endpoint = Environment.GetEnvironmentVariable("AISEARCH_ENDPOINT") ?? string.Empty;
        AISearch_APIKey = Environment.GetEnvironmentVariable("AISEARCH_APIKEY") ?? string.Empty;
        AISearch_Semantic_Configuration = Environment.GetEnvironmentVariable("AISEARCH_SEMANTIC_CONFIG") ?? string.Empty;

        // If any is empty, exit
        if (API_Endpoint == string.Empty || API_Key == string.Empty || API_Version == string.Empty || GPT_Model_Deployment_Name == string.Empty || ADA_Model_Deployment_Name == string.Empty || AISearch_Endpoint == string.Empty || AISearch_APIKey == string.Empty || AISearch_Semantic_Configuration == string.Empty)
        {
            Console.WriteLine("One or more environment variables are missing. Please check the .env file.");
            Environment.Exit(1);
        }

    }

}