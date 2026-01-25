from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_key: str
    
    # Gemini API
    gemini_api_key: str
    
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

@lru_cache()
def get_settings():
    return Settings()
