#!/usr/bin/env python3
"""
Simple migration script to add metadata column to sections table
"""

import os
from supabase import create_client, Client
from config import get_settings

def run_migration():
    """Add metadata column to sections table if it doesn't exist"""
    settings = get_settings()
    
    # Initialize Supabase client
    supabase: Client = create_client(settings.supabase_url, settings.supabase_key)
    
    try:
        # Try to add the metadata column
        result = supabase.rpc('exec', {
            'sql': '''
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'sections' AND column_name = 'metadata'
                ) THEN
                    ALTER TABLE sections ADD COLUMN metadata JSONB;
                    RAISE NOTICE 'Added metadata column to sections table';
                ELSE
                    RAISE NOTICE 'Metadata column already exists in sections table';
                END IF;
            END $$;
            '''
        }).execute()
        
        print("✅ Migration completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        print("The sections table will work without metadata column for now.")
        return False

if __name__ == "__main__":
    run_migration()