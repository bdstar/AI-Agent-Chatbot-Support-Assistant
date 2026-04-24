import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application configuration loaded from environment variables."""

    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    # PostgreSQL
    DB_NAME: str = os.getenv("DB_NAME", "support_agent")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "123")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")

    # Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DOCUMENTS_DIR: str = os.path.join(BASE_DIR, "Documents")
    CHROMA_DIR: str = os.path.join(BASE_DIR, "chroma_db")

    # RAG Settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RESULTS: int = 5

    @property
    def db_connection_string(self) -> str:
        return (
            f"dbname={self.DB_NAME} "
            f"user={self.DB_USER} "
            f"password={self.DB_PASSWORD} "
            f"host={self.DB_HOST} "
            f"port={self.DB_PORT}"
        )


settings = Settings()
