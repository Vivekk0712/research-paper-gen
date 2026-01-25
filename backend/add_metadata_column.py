#!/usr/bin/env python3
"""
Add metadata column to sections table
"""

from supabase import create_client
from config import get_settings

def add_metadata_column():
    settings = get_settings()
    supabase = create_client(settings.supabase_url, settings.supabase_key)
    
    try:
        # First, let's check if the column exists by trying to select it
        try:
            result = supabase.table("sections").select("metadata").limit(1).execute()
            print("✅ Metadata column already exists")
            return True
        except Exception:
            print("📝 Metadata column doesn't exist, will create it...")
        
        # Try to add the column using a simple approach
        # Note: Supabase might not allow direct DDL, so we'll handle this gracefully
        print("⚠️  Cannot add column via API. Please run this SQL in your Supabase dashboard:")
        print("\nSQL to run in Supabase SQL Editor:")
        print("ALTER TABLE sections ADD COLUMN IF NOT EXISTS metadata JSONB;")
        print("\nOr the system will work without metadata for now.")
        
        return False
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    add_metadata_column()