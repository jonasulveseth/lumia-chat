#!/usr/bin/env python3
"""
Start script for Lumia application.
"""
import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    print("🧠 Starting Lumia - AI Chat Service")
    print(f"📡 Brain API: {settings.brain_api_url}")
    print(f"🤖 LLM Model: {settings.llm_model}")
    print(f"🔗 Embedding Model: {settings.embedding_model}")
    print(f"🌐 Server: http://{settings.host}:{settings.port}")
    print(f"📚 API Docs: http://{settings.host}:{settings.port}/docs")
    print("=" * 50)
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    ) 