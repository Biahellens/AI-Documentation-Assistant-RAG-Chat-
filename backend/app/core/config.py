from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "RAG Chat"
    DEBUG: bool = False

    # Embeddings
    # Why all-MiniLM-L6-v2?
    #   - 384-dim vectors: small & fast (vs 1536 for OpenAI ada-002)
    #   - Strong semantic similarity on technical English text
    #   - No API key required — fully local inference
    #   - Trade-off: slightly lower quality than ada-002 on very complex queries
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # Vector DB (Chroma)
    # Why Chroma over FAISS?
    #   - Native persistence without manual save/load
    #   - Metadata filtering out of the box
    #   - Trade-off: slightly more overhead than raw FAISS for huge datasets
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    CHROMA_COLLECTION: str = "documents"

    # Chunking strategy
    # 512 tokens ~ 380 words — enough context for a full paragraph
    # 64 token overlap prevents losing context at boundaries
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64

    # RAG
    TOP_K_RESULTS: int = 5       # number of chunks to retrieve per query
    MEMORY_WINDOW: int = 6       # number of conversation turns to keep in context

    # LLM
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4o-mini"

    # Logging
    TOKEN_LOG_FILE: str = "./logs/token_usage.jsonl"

    class Config:
        env_file = ".env"


settings = Settings()
