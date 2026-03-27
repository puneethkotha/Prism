from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://prism:prism@localhost:5432/prism"
    database_url_sync: str = "postgresql+psycopg2://prism:prism@localhost:5432/prism"
    anthropic_api_key: str = ""
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384
    llm_model: str = "claude-sonnet-4-20250514"
    search_top_k_default: int = 10
    cors_origins: list[str] = ["http://localhost:5173", "https://puneethkotha.github.io"]

    class Config:
        env_file = ".env"

    @property
    def psycopg2_dsn(self) -> str:
        """Raw DSN for psycopg2 — strips the SQLAlchemy driver prefix."""
        return self.database_url_sync.replace("postgresql+psycopg2://", "postgresql://")


settings = Settings()
