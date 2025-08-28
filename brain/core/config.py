"""
Configuration settings for Brain RAG service.
"""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class BrainSettings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Ollama settings
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    embedding_model: str = Field(default="nomic-embed-text", env="EMBEDDING_MODEL")
    llm_model: str = Field(default="qwen3:14b", env="LLM_MODEL")
    
    # ChromaDB settings
    chroma_persist_directory: str = Field(default="./chroma_db", env="CHROMA_PERSIST_DIRECTORY")
    
    # App settings
    debug: bool = Field(default=True, env="DEBUG")
    host: str = Field(default="0.0.0.0", env="BRAIN_HOST")
    port: int = Field(default=8000, env="BRAIN_PORT")
    
    # RAG settings
    similarity_threshold: float = Field(default=0.7, env="SIMILARITY_THRESHOLD")
    max_results: int = Field(default=5, env="MAX_RESULTS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = BrainSettings() 