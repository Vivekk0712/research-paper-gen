#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for database to be ready..."
while ! nc -z database 5432; do
  sleep 1
done
echo "Database is ready!"

# Run database migrations if needed
echo "Running database setup..."
python -c "
import sys
sys.path.append('/app')
from database import supabase
print('Database connection test passed!')
"

# Download and cache the embedding model
echo "Downloading embedding model..."
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
print('Embedding model cached successfully!')
"

# Start the application
echo "Starting IEEE Paper Generator Backend..."
exec "$@"