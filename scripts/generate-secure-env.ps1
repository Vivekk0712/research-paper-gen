# Generate secure environment file for IEEE Paper Generator (Windows PowerShell)
# This script creates a .env file with secure random passwords

Write-Host "🔐 Generating secure environment configuration..." -ForegroundColor Green

# Function to generate secure password
function Generate-SecurePassword {
    $bytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RNGCryptoServiceProvider]::new()
    $rng.GetBytes($bytes)
    $password = [Convert]::ToBase64String($bytes) -replace '[=+/]', '' | Select-Object -First 25
    $rng.Dispose()
    return $password
}

# Check if .env already exists
if (Test-Path ".env") {
    Write-Host "⚠️  .env file already exists!" -ForegroundColor Yellow
    $overwrite = Read-Host "Do you want to overwrite it? (y/N)"
    if ($overwrite -ne "y" -and $overwrite -ne "Y") {
        Write-Host "❌ Aborted. Existing .env file preserved." -ForegroundColor Red
        exit 1
    }
}

# Generate secure password
$dbPassword = Generate-SecurePassword

# Create .env file content
$envContent = @"
# IEEE Paper Generator - Environment Configuration
# Generated on $(Get-Date)

# Database Configuration
DB_PASSWORD=$dbPassword

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
"@

# Write to .env file
$envContent | Out-File -FilePath ".env" -Encoding UTF8

Write-Host "✅ Secure .env file created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Next steps:" -ForegroundColor Cyan
Write-Host "1. Edit .env file and add your GEMINI_API_KEY"
Write-Host "2. Keep this file secure and never commit it to git"
Write-Host "3. Run 'make up' to start the application"
Write-Host ""
Write-Host "🔑 Generated secure database password: $dbPassword" -ForegroundColor Yellow
Write-Host "   (This password is already saved in your .env file)"
Write-Host ""
Write-Host "⚠️  IMPORTANT: Keep your .env file secure and never share it publicly!" -ForegroundColor Red