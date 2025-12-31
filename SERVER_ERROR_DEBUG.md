# Server Error Debugging Guide

## Problem
Getting a server error (500) when trying to register after deployment.

## Changes Made

### 1. Enhanced Error Logging
- Added global exception handler in `main.py` that logs full tracebacks
- All exceptions are now logged with:
  - Error message
  - Request path and method
  - Full Python traceback
  - Endpoint name

### 2. Improved Error Handling
- Better exception catching in registration route
- Database connection errors are properly handled
- Validation errors are separated from database errors

## How to Debug

### Step 1: Check Application Logs

Look for error messages in your deployment platform's logs (Railway/Render/etc). The logs will now show:

```
Unhandled exception in auth.register: [error message]
Request path: /register
Request method: POST
Traceback:
[full Python traceback]
```

### Step 2: Check Health Endpoint

Visit `https://your-deployment-url/health` to verify:
- Database connection status
- Whether User table exists
- List of all tables

**Expected Response:**
```json
{
  "status": "ok",
  "database": "connected",
  "tables": ["user", "waste_item", ...],
  "user_table_exists": true,
  "user_count": 0
}
```

### Step 3: Common Issues and Solutions

#### Issue 1: Database Table Doesn't Exist

**Symptoms:**
- Health endpoint shows `"user_table_exists": false`
- Logs show: "Database table 'user' does not exist"

**Solution:**
Run database initialization:
```bash
python -c "from app import db, app; with app.app_context(): db.create_all()"
```

Or use:
```bash
python recreate_db.py
```

#### Issue 2: Database Connection Error

**Symptoms:**
- Health endpoint shows `"database": "disconnected"`
- Logs show connection errors

**Solution:**
1. Check `DATABASE_URL` environment variable is set correctly
2. Verify database is accessible from deployment platform
3. Check database credentials
4. For Railway: Ensure database service is running
5. For Render: Check database status in dashboard

#### Issue 3: CSRF Token Error

**Symptoms:**
- Logs show: "CSRF token missing" or "CSRF validation failed"
- Form submission fails silently

**Solution:**
1. Ensure `SESSION_SECRET` environment variable is set
2. Check that `{{ form.hidden_tag() }}` is in the template (it is)
3. Verify cookies are enabled in browser
4. Check if session storage is working

#### Issue 4: Import Error

**Symptoms:**
- Logs show: "No module named 'X'"
- Import errors in traceback

**Solution:**
1. Check `requirements.txt` includes all dependencies
2. Run `pip install -r requirements.txt` in deployment
3. Verify all Python packages are installed

#### Issue 5: Missing Environment Variables

**Symptoms:**
- Logs show: "DATABASE_URL not found"
- Application falls back to SQLite

**Solution:**
Set required environment variables:
- `DATABASE_URL` - Database connection string
- `SESSION_SECRET` - Flask secret key
- `GEMINI_API_KEY` - Google Gemini API key (required for app to work)

## Testing Registration

1. **Check Health**: Visit `/health` endpoint
2. **Check Logs**: Monitor application logs during registration attempt
3. **Try Registration**: Fill out registration form and submit
4. **Check Logs Again**: Look for error messages in logs
5. **Verify Database**: Check if user was created (if registration seemed to succeed)

## What to Look For in Logs

### Successful Registration:
```
User registered successfully: username (email@example.com)
```

### Database Error:
```
Database error during registration: [error details]
Integrity error during registration: [error details]
```

### Validation Error:
```
Form validation errors: {'field': ['error message']}
```

### Connection Error:
```
Error checking/creating database tables: [error details]
Database table 'user' does not exist or is not accessible: [error details]
```

## Next Steps

1. **Deploy the updated code** with enhanced error handling
2. **Check the logs** when registration fails
3. **Share the error message** from logs to identify the exact issue
4. **Use the health endpoint** to verify database status

## Files Modified

1. `main.py` - Added global exception handler with detailed logging
2. `auth.py` - Improved validation error handling
3. `routes.py` - Enhanced 500 error handler

The error handler will now capture and log the exact error, making it much easier to diagnose the issue.

