"""
Configuration settings for Lumia application.
"""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
	"""Application settings loaded from environment variables."""
	
	# Ollama settings
	ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
	llm_model: str = Field(default="qwen3:14b", env="LLM_MODEL")
	embedding_model: str = Field(default="nomic-embed-text", env="EMBEDDING_MODEL")
	gatekeeper_model: str = Field(default="qwen3:1.7b", env="GATEKEEPER_MODEL")
	
	# LLM Prompt settings
	system_prompt: str = Field(
		default="""
Du är Lumia – en varm, nyfiken och pålitlig samtalspartner. Du svarar alltid på svenska.

Samtalsstil (viktigt):
- Håll det kort: 1–3 meningar. Använd enkel Markdown sparsamt.
- Var ett bollplank: svara, relatera kort till något relevant från minnet, och ställ 1 fokuserad följdfråga som för samtalet framåt.
- Sammanfatta inte allt om det inte efterfrågas. Undvik upprepningar och onödig utfyllnad.

Minne du kan använda:
- Kortsiktigt minne: senaste utbytena i konversationen.
- Långsiktigt minne ("Brain"): tidigare konversationer/anteckningar per användare (med datum). Om något är relevant, väv in det mycket kort.

Datum/tid:
- Du känner till dagens datum (injiceras av systemet). Om frågan är tidsbaserad (t.ex. “igår”), resonera utifrån rätt dag. Visa datum bara om det behövs eller efterfrågas.

Transparens:
- Avslöja inte interna processer. Visa bara slutsvaret.
- Om inget relevant minne hittas: säg kort “Jag hittar inget i mina anteckningar om det just nu.” och ställ en framåtriktad fråga.
		""",
		env="SYSTEM_PROMPT"
	)
	
	# RAG settings
	use_rag: bool = Field(default=True, env="USE_RAG")
	brain_api_url: str = Field(default="http://127.0.0.1:8000", env="BRAIN_API_URL")
	
	# Output filtering
	strip_think_sections: bool = Field(default=True, env="STRIP_THINK")
	think_probe_max_chars: int = Field(default=4096, env="THINK_PROBE_MAX_CHARS")
	include_dates_by_default: bool = Field(default=False, env="INCLUDE_DATES_BY_DEFAULT")
	
	# Database settings
	database_url: str = Field(default="sqlite:///./lumia.db", env="DATABASE_URL")
	
	# JWT settings
	secret_key: str = Field(default="your-secret-key-here-change-in-production", env="SECRET_KEY")
	algorithm: str = Field(default="HS256", env="ALGORITHM")
	access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
	
	# ChromaDB settings
	chroma_persist_directory: str = Field(default="./chroma_db", env="CHROMA_PERSIST_DIRECTORY")
	
	# App settings
	debug: bool = Field(default=True, env="DEBUG")
	host: str = Field(default="0.0.0.0", env="HOST")
	port: int = Field(default=8002, env="PORT")
	
	class Config:
		env_file = ".env"
		case_sensitive = False


# Global settings instance
settings = Settings() 