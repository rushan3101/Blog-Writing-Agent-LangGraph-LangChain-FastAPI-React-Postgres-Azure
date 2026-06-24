from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    GOOGLE_API_KEY: str
    OPENAI_API_KEY: str
    TAVILY_API_KEY: str
    PUTER_TOKEN: str

    DATABASE_URL: str
    API_BASE_URL: str
    FRONTEND_URL: str

    AZURE_STORAGE_CONNECTION_STRING: str
    AZURE_STORAGE_CONTAINER_NAME: str
    BLOB_ACCOUNT_URL: str

    ROUTER: str
    RESEARCH: str
    PLANNER: str
    TASK: str
    WORKER: str
    IMAGE_DECIDER: str
    IMAGE: str

    LANGCHAIN_TRACING_V2 : str
    LANGCHAIN_ENDPOINT : str
    LANGCHAIN_API_KEY : str
    LANGCHAIN_PROJECT : str

    class Config:
        env_file = ".env"

settings = Settings()