#!/bin/bash

# Generate secure environment file for IEEE Paper Generator
# This script creates a .env file with secure random passwords

set -e

echo "🔐 Generating secure environment configuration..."

# Generate secure random password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Check if .env already exists
if [ -f .env ]; then
    echo "⚠️  .env file already exists!"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Aborted. Existing .env file preserved."
        exit 1
    fi
fi

# Generate secure password
DB_PASSWORD=$(generate_password)

# Create .env file
cat > .env << EOF
# IEEE Paper Generator - Environment Configuration
# Generated on $(date)

# Database Configuration
DB_PASSWORD=${DB_PASSWORD}

# Supabase Configuration (Optional - for external Supabase)
# Leave empty to use local PostgreSQL database
SUPABASE_KEY=

# AI API Configuration (REQUIRED)
# Get your API key from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# Application Settings
DEBUG=false
APP_NAME=IEEE Paper Generator
NODE_ENV=production

# Security Note: Never commit this file to version control!
# This file contains sensitive credentials.
EOF

echo "✅ Secure .env file created successfully!"
echo ""
echo "📝 Next steps:"
echo "1. Edit .env file and add your GEMINI_API_KEY"
echo "2. Keep this file secure and never commit it to git"
echo "3. Run 'make up' to start the application"
echo ""
echo "🔑 Generated secure database password: ${DB_PASSWORD}"
echo "   (This password is already saved in your .env file)"
echo ""
echo "⚠️  IMPORTANT: Keep your .env file secure and never share it publicly!"