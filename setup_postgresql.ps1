# PostgreSQL Setup Script for ReGenWorks (Windows PowerShell)
# This script helps set up the PostgreSQL database connection

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ReGenWorks PostgreSQL Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if PostgreSQL is installed
Write-Host "Checking PostgreSQL installation..." -ForegroundColor Yellow
try {
    $psqlVersion = psql --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ PostgreSQL is installed" -ForegroundColor Green
        Write-Host "  $psqlVersion" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ PostgreSQL not found in PATH" -ForegroundColor Red
    Write-Host "  Please install PostgreSQL from: https://www.postgresql.org/download/windows/" -ForegroundColor Yellow
    Write-Host "  Or ensure PostgreSQL bin directory is in your PATH" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        exit 1
    }
}

Write-Host ""

# Get database connection details
Write-Host "Enter PostgreSQL connection details:" -ForegroundColor Yellow
Write-Host ""

$DB_HOST = Read-Host "Database Host [localhost]"
if ([string]::IsNullOrWhiteSpace($DB_HOST)) {
    $DB_HOST = "localhost"
}

$DB_PORT = Read-Host "Database Port [5432]"
if ([string]::IsNullOrWhiteSpace($DB_PORT)) {
    $DB_PORT = "5432"
}

$DB_NAME = Read-Host "Database Name [regenworks]"
if ([string]::IsNullOrWhiteSpace($DB_NAME)) {
    $DB_NAME = "regenworks"
}

$DB_USER = Read-Host "Database Username [postgres]"
if ([string]::IsNullOrWhiteSpace($DB_USER)) {
    $DB_USER = "postgres"
}

$securePassword = Read-Host "Database Password" -AsSecureString
$DB_PASS = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
)

Write-Host ""

# Test connection
Write-Host "Testing database connection..." -ForegroundColor Yellow
$env:PGPASSWORD = $DB_PASS
$testConnection = psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "SELECT 1;" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Connection successful!" -ForegroundColor Green
} else {
    Write-Host "✗ Connection failed!" -ForegroundColor Red
    Write-Host "  Error: $testConnection" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please check:" -ForegroundColor Yellow
    Write-Host "  1. PostgreSQL is running" -ForegroundColor Yellow
    Write-Host "  2. Host, port, username, and password are correct" -ForegroundColor Yellow
    Write-Host "  3. PostgreSQL allows connections from this host" -ForegroundColor Yellow
    exit 1
}

# Create database if it doesn't exist
Write-Host ""
Write-Host "Checking if database '$DB_NAME' exists..." -ForegroundColor Yellow
$dbExists = psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" 2>&1

if ($dbExists -eq "1") {
    Write-Host "✓ Database '$DB_NAME' already exists" -ForegroundColor Green
} else {
    Write-Host "Creating database '$DB_NAME'..." -ForegroundColor Yellow
    $createDb = psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME WITH ENCODING 'UTF8';" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Database '$DB_NAME' created successfully!" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to create database!" -ForegroundColor Red
        Write-Host "  Error: $createDb" -ForegroundColor Red
        exit 1
    }
}

# Generate DATABASE_URL
$DB_URL = "postgresql://$DB_USER`:$DB_PASS@$DB_HOST`:$DB_PORT/$DB_NAME"

# URL encode special characters in password
$DB_URL = $DB_URL -replace '#', '%23'
$DB_URL = $DB_URL -replace '@', '%40'
$DB_URL = $DB_URL -replace '%', '%25'
$DB_URL = $DB_URL -replace '&', '%26'

Write-Host ""
Write-Host "Generated DATABASE_URL:" -ForegroundColor Cyan
Write-Host "  postgresql://$DB_USER`:***@$DB_HOST`:$DB_PORT/$DB_NAME" -ForegroundColor Gray
Write-Host ""

# Create or update .env file
$envFile = ".env"
$envExample = ".env.example"

if (-not (Test-Path $envFile)) {
    if (Test-Path $envExample) {
        Write-Host "Creating .env file from .env.example..." -ForegroundColor Yellow
        Copy-Item $envExample $envFile
    } else {
        Write-Host "Creating new .env file..." -ForegroundColor Yellow
        New-Item -ItemType File -Path $envFile | Out-Null
    }
}

# Generate SESSION_SECRET if not exists
$sessionSecret = python -c "import secrets; print(secrets.token_hex(32))" 2>&1
if ($LASTEXITCODE -ne 0) {
    $sessionSecret = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | ForEach-Object {[char]$_})
}

# Update .env file
Write-Host "Updating .env file..." -ForegroundColor Yellow

$envContent = Get-Content $envFile -Raw -ErrorAction SilentlyContinue

if ($envContent -match "DATABASE_URL=.*") {
    $envContent = $envContent -replace "DATABASE_URL=.*", "DATABASE_URL=$DB_URL"
} else {
    $envContent += "`n# Database Configuration`nDATABASE_URL=$DB_URL`n"
}

if ($envContent -notmatch "SESSION_SECRET=.*") {
    $envContent += "`n# Flask Configuration`nSESSION_SECRET=$sessionSecret`n"
}

Set-Content -Path $envFile -Value $envContent

Write-Host "✓ .env file updated!" -ForegroundColor Green

# Set environment variable for current session
$env:DATABASE_URL = $DB_URL
Write-Host "✓ DATABASE_URL set for current session" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Initialize database tables:" -ForegroundColor White
Write-Host "   python recreate_db.py" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Start the application:" -ForegroundColor White
Write-Host "   python main.py" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Verify connection:" -ForegroundColor White
Write-Host "   Visit http://localhost:5000/health" -ForegroundColor Gray
Write-Host ""

