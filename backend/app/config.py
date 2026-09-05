from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://lenny:lenny@localhost:5432/lenny_growth"

    default_llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"

    groq_api_key: str = ""
    groq_model: str = "llama-3.1-70b-versatile"

    embedding_model: str = "all-MiniLM-L6-v2"
    top_k: int = 5
    similarity_threshold: float = 0.65

    cors_origins: str = "http://localhost:5173"

    class Config:
        env_file = ("../.env", ".env")
        extra = "ignore"


settings = Settings()
