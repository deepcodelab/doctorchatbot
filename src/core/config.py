import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "Global Chatbot Service"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    LLM_PROVIDER: str = "local"

settings = Settings()