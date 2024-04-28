from dotenv import load_dotenv
import os


class AgentSettings:
    """This class is used to load the settings from the .env file."""
    def __init__(self):
        load_dotenv()
        self.api_endpoint = os.getenv("OPENAI_URI")
        self.api_key = os.getenv("OPENAI_KEY")
        self.api_version = os.getenv("OPENAI_VERSION")
        self.gpt_model_deployment_name = os.getenv("OPENAI_GPT_DEPLOYMENT")
        self.ada_model_deployment_name = os.getenv("OPENAI_ADA_DEPLOYMENT")
        self.email_URI = os.getenv("EMAIL_URI")
        self.aisearch_endpoint = os.getenv("AISEARCH_ENDPOINT")
        self.aisearch_apikey = os.getenv("AISEARCH_APIKEY")
        self.aisearch_semantic_configuration = os.getenv("AISEARCH_SEMANTIC_CONFIG")
