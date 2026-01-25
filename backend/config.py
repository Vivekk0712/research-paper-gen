from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    # Supabase (can be local PostgreSQL or external Supabase)
    supabase_url: str
    supabase_key: str = ""  # Optional for local PostgreSQL
    
    # Gemini API (for text generation only)
    gemini_api_key: str
    
    # Embedding model settings
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    
    # Application
    app_name: str = "IEEE Paper Generator"
    debug: bool = False
    
    # File upload
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: list = [".pdf", ".docx"]
    upload_dir: str = "uploads"
    
    # RAG settings
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_results: int = 5
    
    # Generation settings
    max_tokens: int = 2000
    temperature: float = 0.7
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure upload directory exists
        os.makedirs(self.upload_dir, exist_ok=True)

@lru_cache()
def get_settings():
    return Settings()
