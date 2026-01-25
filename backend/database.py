from supabase import create_client, Client
from config import get_settings

settings = get_settings()

def get_supabase_client() -> Client:
    """Get Supabase client instance"""
    return create_client(settings.supabase_url, settings.supabase_key)

supabase: Client = get_supabase_client()
