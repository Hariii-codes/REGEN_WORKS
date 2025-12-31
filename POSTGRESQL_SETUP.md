# PostgreSQL Setup Guide for ReGenWorks

This guide will help you connect ReGenWorks to your PostgreSQL database.

## Prerequisites

1. **PostgreSQL installed** on your system
   - Download from: https://www.postgresql.org/download/windows/
   - Or use a cloud PostgreSQL service (Railway, Render, Supabase, etc.)

2. **Python package**: `psycopg2-binary` (already in requirements.txt)

## Option 1: Local PostgreSQL Database

### Step 1: Create Database

**Using psql (Command Line):**
```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE regenworks WITH ENCODING 'UTF8';

# Exit psql
\q
```

**Using pgAdmin (GUI):**
1. Open pgAdmin
2. Right-click on "Databases" → "Create" → "Database"
3. Name: `regenworks`
4. Encoding: `UTF8`
5. Click "Save"

### Step 2: Set DATABASE_URL Environment Variable

**Format:**
```
postgresql://username:password@host:port/database_name
```

**Example:**
```
postgresql://postgres:mypassword@localhost:5432/regenworks
```

**For Windows (PowerShell):**
```powershell
# Set environment variable for current session
$env:DATABASE_URL = "postgresql://postgres:mypassword@localhost:5432/regenworks"

# Or set permanently (User-level)
[System.Environment]::SetEnvironmentVariable("DATABASE_URL", "postgresql://postgres:mypassword@localhost:5432/regenworks", "User")
```

**For Windows (Command Prompt):**
```cmd
set DATABASE_URL=postgresql://postgres:mypassword@localhost:5432/regenworks
```

**Using .env file (Recommended):**
1. Copy `.env.example` to `.env`:
   ```powershell
   copy .env.example .env
   ```

2. Edit `.env` and set:
   ```env
   DATABASE_URL=postgresql://postgres:mypassword@localhost:5432/regenworks
   ```

### Step 3: Initialize Database Tables

Run one of these commands:

```bash
# Option 1: Using recreate_db.py (creates fresh database)
python recreate_db.py

# Option 2: Using migrate_new_features.py (for migrations)
python migrate_new_features.py

# Option 3: Direct SQLAlchemy
python -c "from app import db, app; with app.app_context(): db.create_all()"
```

### Step 4: Verify Connection

Start the application:
```bash
python main.py
```

Check the logs - you should see:
```
Connecting to database: postgresql://*****@*****
Database tables already exist. Found X tables.
```

Or visit the health endpoint:
```
http://localhost:5000/health
```

## Option 2: Cloud PostgreSQL (Railway, Render, Supabase, etc.)

### Railway

1. **Create PostgreSQL Database:**
   - Go to Railway dashboard
   - Click "New" → "Database" → "Add PostgreSQL"
   - Railway will automatically create a `DATABASE_URL` variable

2. **Set Environment Variables:**
   - Railway automatically sets `DATABASE_URL`
   - You can also manually set it in Variables tab

3. **Initialize Database:**
   - Go to your service → Settings → Deploy → Run Commandgit push origin main
   - Run: `python recreate_db.py`

### Render

1. **Create PostgreSQL Database:**
   - Go to Render dashboard
   - Click "New" → "PostgreSQL"
   - Name: `regenworks-db`
   - Render will provide a `DATABASE_URL`

2. **Set Environment Variables:**
   - In your web service settings
   - Add `DATABASE_URL` from the PostgreSQL service
   - Format: `postgresql://user:password@host:port/database`

3. **Initialize Database:**
   - Use Render Shell or run command:
   - `python recreate_db.py`

### Supabase

1. **Get Connection String:**
   - Go to Supabase project → Settings → Database
   - Copy the "Connection string" (URI format)
   - Format: `postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`

2. **Set Environment Variable:**
   - Add `DATABASE_URL` with the connection string

3. **Initialize Database:**
   - Run: `python recreate_db.py`

## Connection String Format

```
postgresql://[username]:[password]@[host]:[port]/[database_name]
```

**Components:**
- `username`: PostgreSQL username (default: `postgres`)
- `password`: PostgreSQL password
- `host`: Database host (localhost for local, or cloud provider host)
- `port`: PostgreSQL port (default: `5432`)
- `database_name`: Database name (e.g., `regenworks`)

**Examples:**

**Local:**
```
postgresql://postgres:mypassword@localhost:5432/regenworks
```

**Cloud (Railway/Render):**
```
postgresql://postgres:password@hostname.railway.app:5432/railway
```

**With special characters in password:**
If your password contains special characters, URL-encode them:
- `@` → `%40`
- `#` → `%23`
- `%` → `%25`
- `&` → `%26`
- etc.

Example:
```
postgresql://postgres:my%40password@localhost:5432/regenworks
```

## Troubleshooting

### Issue: "Connection refused" or "Could not connect to server"

**Solutions:**
1. Check PostgreSQL is running:
   ```bash
   # Windows
   Get-Service postgresql*
   
   # Or check in Services app
   ```

2. Check PostgreSQL is listening on the correct port:
   - Default port: `5432`
   - Check in `postgresql.conf`: `port = 5432`

3. Check firewall settings
4. Verify host and port in connection string

### Issue: "Authentication failed"

**Solutions:**
1. Verify username and password are correct
2. Check `pg_hba.conf` allows connections
3. For local: Try `trust` authentication for testing

### Issue: "Database does not exist"

**Solutions:**
1. Create the database:
   ```sql
   CREATE DATABASE regenworks;
   ```

2. Verify database name in connection string

### Issue: "Table does not exist"

**Solutions:**
1. Initialize database tables:
   ```bash
   python recreate_db.py
   ```

2. Check database connection is working
3. Verify `DATABASE_URL` is set correctly

### Issue: "Module 'psycopg2' not found"

**Solutions:**
1. Install psycopg2-binary:
   ```bash
   pip install psycopg2-binary
   ```

2. Or install from requirements.txt:
   ```bash
   pip install -r requirements.txt
   ```

## Testing Connection

### Method 1: Health Endpoint

Visit: `http://localhost:5000/health`

Should return:
```json
{
  "status": "ok",
  "database": "connected",
  "tables": ["user", "waste_item", ...],
  "user_table_exists": true
}
```

### Method 2: Application Logs

Check startup logs for:
```
Connecting to database: postgresql://*****@*****
Database tables already exist. Found X tables.
```

### Method 3: Python Script

Create `test_db_connection.py`:
```python
from app import app, db
from sqlalchemy import inspect

with app.app_context():
    try:
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"✓ Connected to database")
        print(f"✓ Found {len(tables)} tables: {tables}")
    except Exception as e:
        print(f"✗ Connection failed: {e}")
```

Run: `python test_db_connection.py`

## Next Steps

After connecting to PostgreSQL:

1. ✅ Database connection established
2. ✅ Tables initialized (`python recreate_db.py`)
3. ✅ Test registration works
4. ✅ Check health endpoint shows database connected
5. ✅ Verify data persists after restart

## Security Notes

1. **Never commit `.env` file** - it's already in `.gitignore`
2. **Use strong passwords** for production databases
3. **Use SSL connections** for cloud databases (add `?sslmode=require` to connection string)
4. **Restrict database access** to only necessary IPs
5. **Use environment variables** instead of hardcoding credentials

## Example .env File

```env
# Database Configuration
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/regenworks

# Flask Configuration
SESSION_SECRET=your_random_secret_key_here
FLASK_ENV=development
PYTHONUNBUFFERED=true

# AI API Keys
GEMINI_API_KEY="AIzaSyD0qmPtlkosmbG8qPUUKit6b11slQZsP4s"
```

