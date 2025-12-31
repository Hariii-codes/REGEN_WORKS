# Infrastructure Project Feedback Loop - Requirements & Setup

## Overview
This feature allows users to see how their recycled waste contributes to real infrastructure projects in their community. It includes batch tracking, project linking, and a blockchain-like ledger system.

---

## 📋 Prerequisites

### 1. Database Requirements

#### Database Tables
The following tables must exist in your PostgreSQL database:

**infrastructure_projects**
```sql
CREATE TABLE infrastructure_projects (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(50) UNIQUE NOT NULL,
    project_name VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'planned',  -- planned, in_progress, completed
    location_lat NUMERIC(10, 8) NOT NULL,
    location_lng NUMERIC(11, 8) NOT NULL,
    date_started DATE,
    date_completed DATE,
    total_plastic_required_grams NUMERIC(12, 2),  -- Total weight required (all material types)
    total_plastic_allocated_grams NUMERIC(12, 2) DEFAULT 0,  -- Total weight allocated (all material types)
    project_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Note:** The column names `total_plastic_required_grams` and `total_plastic_allocated_grams` are legacy names but actually store total weight for ALL material types (Plastic, Paper, Metal, Glass, Organic, Textile, Electronic, etc.), not just plastic.

**waste_batches**
```sql
CREATE TABLE waste_batches (
    id SERIAL PRIMARY KEY,
    batch_id VARCHAR(50) UNIQUE NOT NULL,
    total_weight_grams NUMERIC(12, 2) NOT NULL,
    material_type VARCHAR(50) NOT NULL,
    linked_project_id INTEGER REFERENCES infrastructure_projects(id) ON DELETE SET NULL,
    collection_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_date TIMESTAMP,
    status VARCHAR(20) DEFAULT 'collected',  -- collected, processing, allocated, completed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**project_contributors**
```sql
CREATE TABLE project_contributors (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    batch_id INTEGER NOT NULL REFERENCES waste_batches(id) ON DELETE CASCADE,
    contribution_weight_grams NUMERIC(10, 2) NOT NULL,
    contribution_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_top_contributor BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, batch_id)
);
```

**project_ledger**
```sql
CREATE TABLE project_ledger (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL,
    verified_by VARCHAR(100),
    batch_reference VARCHAR(50),
    previous_hash VARCHAR(64),
    block_hash VARCHAR(64) NOT NULL,
    data JSONB,
    firestore_synced BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Database Indexes
```sql
CREATE INDEX idx_waste_batches_project ON waste_batches(linked_project_id);
CREATE INDEX idx_project_contributors_user ON project_contributors(user_id);
CREATE INDEX idx_project_contributors_batch ON project_contributors(batch_id);
CREATE INDEX idx_project_ledger_project ON project_ledger(project_id);
CREATE INDEX idx_project_ledger_synced ON project_ledger(firestore_synced) WHERE firestore_synced = FALSE;
```

---

### 2. Python Dependencies

Add these packages to your `requirements.txt`:

```txt
# Existing dependencies
flask>=2.3.0
flask-login>=0.6.2
flask-sqlalchemy>=3.0.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0

# Firebase/Firestore (optional but recommended)
firebase-admin>=6.2.0

# For UUID generation
uuid  # Built-in, no install needed
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

---

### 3. Firebase/Firestore Setup (Optional but Recommended)

#### Step 1: Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or use existing one
3. Enable Firestore Database

#### Step 2: Generate Service Account Key
1. Go to Project Settings → Service Accounts
2. Click "Generate New Private Key"
3. Download the JSON key file
4. Save it securely (e.g., `firebase-service-account.json`)

#### Step 3: Set Environment Variable
```bash
# Windows (PowerShell)
$env:FIREBASE_SERVICE_ACCOUNT_KEY="path/to/firebase-service-account.json"

# Linux/Mac
export FIREBASE_SERVICE_ACCOUNT_KEY="path/to/firebase-service-account.json"

# Or add to .env file
FIREBASE_SERVICE_ACCOUNT_KEY=firebase-service-account.json
```

#### Step 4: Firestore Security Rules
Set up Firestore rules in Firebase Console:
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /ledger/{projectId}/entries/{entryId} {
      allow read: if true;  // Public read
      allow write: if request.auth != null;  // Authenticated write
    }
  }
}
```

---

### 4. Google Maps API (Optional)

For map previews in the UI:

#### Step 1: Get API Key
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "Maps Embed API"
4. Create API key
5. Restrict key to "Maps Embed API" only

#### Step 2: Set Environment Variable
```bash
# Add to .env or environment
GOOGLE_MAPS_API_KEY=your_api_key_here
```

#### Step 3: Update Flask Config
In `app.py` or `main.py`:
```python
app.config['GOOGLE_MAPS_API_KEY'] = os.environ.get('GOOGLE_MAPS_API_KEY', '')
```

**Note:** Maps will work without API key but show placeholder instead of actual map.

---

### 5. Environment Variables

Create a `.env` file or set these environment variables:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ReGenWorks

# Firebase (optional)
FIREBASE_SERVICE_ACCOUNT_KEY=path/to/firebase-service-account.json

# Google Maps (optional)
GOOGLE_MAPS_API_KEY=your_google_maps_api_key

# Flask
FLASK_ENV=development
FLASK_APP=main.py
SECRET_KEY=your-secret-key-here
```

---

### 6. File Structure

Ensure these files exist:

```
ReGenWorks/
├── models.py                    # Database models (already has InfrastructureProject, WasteBatch, etc.)
├── infrastructure_projects.py   # Routes and logic for infrastructure projects
├── firestore_sync.py           # Firebase/Firestore integration
├── seed_infrastructure_projects.py  # Seed script for sample projects
├── api_definitions.py           # API endpoints (already has project endpoints)
├── main.py                      # App initialization (registers routes)
└── templates/
    ├── infrastructure_projects.html      # Main projects dashboard
    └── infrastructure_project_detail.html # Project detail page
```

---

### 7. Setup Steps

#### Step 1: Database Migration
```bash
# Run database migrations (if using Flask-Migrate)
flask db upgrade

# Or run SQL directly
psql -U postgres -d ReGenWorks -f database_migrations.sql
```

#### Step 2: Seed Sample Projects (Optional)
```bash
python seed_infrastructure_projects.py
```

Or projects will auto-seed when you first visit `/infrastructure-projects`

#### Step 3: Verify Setup
1. Start the Flask app: `python main.py`
2. Log in to your account
3. Navigate to `/infrastructure-projects`
4. You should see sample projects

---

### 8. API Endpoints

The following API endpoints are available:

**GET `/infrastructure-projects`**
- Displays all infrastructure projects
- Requires: Login
- Returns: HTML page with project cards

**GET `/infrastructure-projects/<project_id>`**
- Displays detailed project information
- Requires: Login
- Returns: HTML page with project details

**POST `/api/projects/batch/create`**
- Creates a new waste batch
- Requires: Login, JSON body with batch data
- Returns: JSON response with batch_id

**POST `/api/projects/ledger/update`**
- Adds ledger entry for project update
- Requires: Login, JSON body with project_id, status, etc.
- Returns: JSON response with ledger_id and block_hash

---

### 9. Features

#### ✅ Implemented Features:
- Infrastructure project listing with status badges
- Project detail pages with progress tracking
- User contribution tracking per project
- Top contributor detection (top 10%)
- Batch linking to projects
- Blockchain-like ledger system
- Firestore integration for immutable records
- Google Maps location preview (optional)
- Auto-seeding of sample projects

#### 🔄 How It Works:
1. **Waste Collection**: When waste is collected, it's aggregated into batches
2. **Batch Creation**: Batches are created with material type and weight
3. **Project Linking**: Batches can be linked to infrastructure projects
4. **Contribution Tracking**: User contributions are tracked automatically
5. **Ledger Entry**: Each batch-project link creates an immutable ledger entry
6. **Firestore Sync**: Ledger entries are synced to Firestore for permanence
7. **Top Contributors**: Top 10% contributors get "Community Builder" badge

---

### 10. Troubleshooting

#### Issue: "No infrastructure projects found"
**Solution**: Run the seed script:
```bash
python seed_infrastructure_projects.py
```

#### Issue: Firebase/Firestore not working
**Solution**: 
- Check if `FIREBASE_SERVICE_ACCOUNT_KEY` is set correctly
- Verify service account key file exists and is valid
- Check Firestore rules allow writes
- Feature will work without Firebase (ledger entries just won't sync)

#### Issue: Google Maps not showing
**Solution**:
- Set `GOOGLE_MAPS_API_KEY` environment variable
- Enable "Maps Embed API" in Google Cloud Console
- Maps will show placeholder if API key is missing (still functional)

#### Issue: Database errors
**Solution**:
- Ensure all tables are created (run migrations)
- Check database connection string is correct
- Verify foreign key relationships are set up

---

### 11. Testing

#### Manual Testing Checklist:
- [ ] Visit `/infrastructure-projects` - should show projects
- [ ] Click "View Details" on a project - should show detail page
- [ ] Check user contribution displays correctly
- [ ] Verify top contributor badge appears (if applicable)
- [ ] Test batch creation via API
- [ ] Test ledger update via API
- [ ] Verify Firestore sync (if Firebase is configured)

---

### 12. Production Deployment

#### Additional Requirements for Production:

1. **Database**: Use managed PostgreSQL (e.g., AWS RDS, Render PostgreSQL)
2. **Firebase**: Use production Firebase project with proper security rules
3. **Environment Variables**: Set all environment variables in production environment
4. **API Keys**: Restrict Google Maps API key to your domain
5. **Security**: Enable Firestore authentication for writes
6. **Monitoring**: Set up logging for Firestore sync failures

---

## 📝 Summary

**Minimum Requirements:**
- ✅ PostgreSQL database with required tables
- ✅ Python dependencies installed
- ✅ Flask app running

**Optional but Recommended:**
- 🔥 Firebase/Firestore for immutable ledger
- 🗺️ Google Maps API for map previews

**The feature will work without Firebase and Google Maps**, but with limited functionality (no Firestore sync, placeholder maps instead of real maps).

---

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up database:**
   ```bash
   # Tables should already exist if you ran migrations
   # If not, create them using the SQL above
   ```

3. **Run seed script (optional):**
   ```bash
   python seed_infrastructure_projects.py
   ```

4. **Start the app:**
   ```bash
   python main.py
   ```

5. **Visit the page:**
   - Log in to your account
   - Navigate to "Infrastructure Projects" in the menu
   - You should see sample projects!

---

## 📞 Support

If you encounter issues:
1. Check the error logs
2. Verify all environment variables are set
3. Ensure database tables exist
4. Check Firebase service account key (if using Firestore)
5. Verify Google Maps API key (if using maps)

