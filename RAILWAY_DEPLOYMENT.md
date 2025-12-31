# Railway Deployment Guide for ReGenWorks

This guide will help you deploy ReGenWorks to Railway.

## Prerequisites

- A Railway account (sign up at [railway.app](https://railway.app))
- A GitHub repository with your ReGenWorks code
- Google Gemini API key
- Firebase service account JSON (if using Firebase features)

## Step 1: Create a New Project on Railway

1. Go to [railway.app](https://railway.app) and sign in
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your ReGenWorks repository

## Step 2: Set Environment Variables

Click on your project, then go to **Variables** tab and add the following environment variables:

### Required Environment Variables

#### 1. Database Configuration

**For SQLite (Quick Start):**
```
DATABASE_URL=sqlite:///data.db
```

**For PostgreSQL (Recommended for Production):**
```
DATABASE_URL=<your_postgresql_connection_string>
```

To get a PostgreSQL database on Railway:
- Click "New" → "Database" → "Add PostgreSQL"
- Railway will automatically create a `DATABASE_URL` variable
- Or use your own PostgreSQL connection string in the format:
  ```
  postgresql://username:password@host:port/database_name
  ```

#### 2. Firebase Service Account (Optional - if using Firebase features)

```
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"your-project-id","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"...","client_id":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"...","universe_domain":"googleapis.com"}
```

**Important:** 
- This should be the entire JSON content as a single-line string (no line breaks)
- You can get this from Firebase Console → Project Settings → Service Accounts
- Generate a new private key and copy the entire JSON content
- Remove all line breaks and format it as a single line
- Keep all quotes escaped properly
- Example: Copy the JSON from `firebase-service-account.json` file and convert it to a single line

#### 3. Google Gemini API Key

```
GEMINI_API_KEY="AIzaSyD0qmPtlkosmbG8qPUUKit6b11slQZsP4s"
```

Get your API key from:
- [Google AI Studio](https://makersuite.google.com/app/apikey)
- Or [Google Cloud Console](https://console.cloud.google.com/)

### Optional Environment Variables

#### 4. Flask Secret Key (for sessions)

```
SESSION_SECRET=your_random_secret_key_here
```

Generate a random secret:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

#### 5. Flask Environment

```
FLASK_ENV=production
```

#### 6. Python Unbuffered (for logging)

```
PYTHONUNBUFFERED=true
```

## Step 3: Configure Build Settings

Railway will automatically detect your Python project. Make sure you have:

1. **`requirements.txt`** in your project root
2. **`Procfile`** or **`runtime.txt`** (optional)

### Procfile (if using)

Create a `Procfile` in your project root:
```
web: gunicorn --bind 0.0.0.0:$PORT --timeout=120 --workers=2 main:app
```

Or Railway will auto-detect and use:
```
web: python main.py
```

## Step 4: Deploy

1. Railway will automatically deploy when you push to your GitHub repository
2. Or click "Deploy" in the Railway dashboard
3. Wait for the build to complete
4. Your app will be available at the generated Railway URL

## Step 5: Initialize Database

After deployment, you may need to initialize the database:

1. Go to your Railway project
2. Click on your service
3. Go to "Settings" → "Deploy" → "Run Command"
4. Run database initialization:

**For SQLite:**
```bash
python recreate_db.py
```

**For PostgreSQL:**
```bash
python migrate_new_features.py
```

Or run migrations directly:
```bash
python -c "from app import db, app; with app.app_context(): db.create_all()"
```

## Environment Variables Summary

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Database connection string (SQLite or PostgreSQL) |
| `GEMINI_API_KEY` | Yes | Google Gemini API key for AI analysis |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Optional | Firebase service account JSON (if using Firebase) |
| `SESSION_SECRET` | Recommended | Secret key for Flask sessions |
| `FLASK_ENV` | Optional | Set to `production` for production deployment |
| `PYTHONUNBUFFERED` | Optional | Set to `true` for better logging |

## Troubleshooting

### Database Connection Issues

- Make sure `DATABASE_URL` is correctly formatted
- For PostgreSQL, ensure the database is accessible from Railway's network
- Check that the database exists and credentials are correct

### Firebase JSON Format

- The `FIREBASE_SERVICE_ACCOUNT_JSON` must be valid JSON
- It should be a single-line string (no line breaks)
- Escape quotes properly if pasting manually
- **How to convert your JSON file to a single line:**
  1. Open your `firebase-service-account.json` file
  2. Copy the entire JSON content
  3. Use an online JSON minifier or remove all line breaks manually
  4. Paste the single-line JSON as the value for `FIREBASE_SERVICE_ACCOUNT_JSON`
  
  **Example using Python:**
  ```python
  import json
  with open('firebase-service-account.json', 'r') as f:
      json_data = json.load(f)
  single_line = json.dumps(json_data)
  print(single_line)  # Copy this output
  ```

### Build Failures

- Check that `requirements.txt` includes all dependencies
- Ensure Python version is compatible (3.9+)
- Check build logs in Railway dashboard for specific errors

### Application Not Starting

- Verify all required environment variables are set
- Check application logs in Railway dashboard
- Ensure the port is configured correctly (Railway sets `$PORT` automatically)

## Additional Resources

- [Railway Documentation](https://docs.railway.app)
- [Railway Discord](https://discord.gg/railway)
- [Flask Deployment Guide](https://flask.palletsprojects.com/en/latest/deploying/)

## Notes

- Railway provides a free tier with limited resources
- For production, consider upgrading to a paid plan
- Database backups are recommended for production deployments
- Monitor your API usage for Gemini to avoid exceeding quotas

