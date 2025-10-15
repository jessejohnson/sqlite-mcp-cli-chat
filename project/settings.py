import os
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()

@dataclass
class Settings:
    LLM_SERVICE: str = os.environ["LLM_SERVICE"]
    IS_DEBUG: bool = os.environ["IS_DEBUG"].lower() == "true"
    MODEL_NAME: str = os.environ["MODEL_NAME"]
    MAX_TOKENS: int = os.environ["MAX_TOKENS"]
    SERVER_DB_PATH: str = os.environ["SERVER_DB_PATH"]
    SERVER_RESOURCE_DIR: str = os.environ["SERVER_RESOURCE_DIR"]
    LOG_DIR: str = os.environ["LOG_DIR"]

settings = Settings()