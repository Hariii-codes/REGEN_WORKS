# ReGenWorks Integration Roadmap
## Step-by-Step Implementation Guide

---

## 📋 PREREQUISITES

- PostgreSQL database running
- Firebase project configured
- Google Maps API key
- TFLite model file for waste classification
- Python 3.11+ environment
- Node.js 18+ (for web frontend)
- Android Studio (for Android app)

---

## 🗄️ PHASE 1: DATABASE SETUP (Day 1-2)

### Step 1.1: Run Database Migrations
```bash
# Connect to PostgreSQL
psql -U postgres -d ReGenWorks

# Run migration script
\i database_migrations.sql

# Verify tables created
\dt

# Check indexes
\di
```

### Step 1.2: Verify Schema
```sql
-- Check new tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
    'user_plastic_footprint_monthly',
    'plastic_footprint_scans',
    'material_weight_lookup',
    'localization_strings',
    'waste_batches',
    'infrastructure_projects',
    'project_contributors',
    'project_ledger'
);

-- Verify triggers
SELECT trigger_name FROM information_schema.triggers;
```

### Step 1.3: Seed Initial Data
```sql
-- Verify weight lookup data inserted
SELECT * FROM material_weight_lookup;

-- Verify localization strings inserted
SELECT COUNT(*) FROM localization_strings WHERE language = 'en';
```

**✅ Completion Criteria:**
- All tables created with correct schema
- Triggers active
- Initial seed data loaded
- Indexes created

---

## 🔧 PHASE 2: BACKEND API INTEGRATION (Day 3-5)

### Step 2.1: Update Models
- ✅ Models already updated in `models.py`
- Verify imports work:
```python
from models import (
    UserPlasticFootprintMonthly,
    PlasticFootprintScan,
    MaterialWeightLookup,
    LocalizationString,
    InfrastructureProject,
    WasteBatch,
    ProjectContributor,
    ProjectLedger
)
```

### Step 2.2: Register API Routes
Update `main.py` or `app.py`:
```python
from api_definitions import register_api_routes

# After app initialization
register_api_routes(app)
```

### Step 2.3: Create Service Modules
Create `footprint_service.py`:
```python
from models import MaterialWeightLookup, UserPlasticFootprintMonthly
from app import db
from datetime import date

def estimate_weight_from_ml(material_type, category=None, confidence_score=0.0):
    """Estimate weight from lookup table"""
    lookup = MaterialWeightLookup.query.filter_by(
        material_type=material_type
    ).first()
    
    if lookup:
        return float(lookup.average_weight_grams)
    return 25.0  # Default fallback

def calculate_badge_level(total_weight_grams):
    """Calculate badge level"""
    if total_weight_grams >= 10000:
        return 'Champion'
    elif total_weight_grams >= 5000:
        return 'Gold'
    elif total_weight_grams >= 2000:
        return 'Silver'
    return 'Bronze'
```

### Step 2.4: Integrate with Existing Scan Flow
Update `routes.py` in the `index()` function:
```python
# After waste_item is created and analyzed
if current_user.is_authenticated:
    from api_definitions import update_footprint
    from footprint_service import estimate_weight_from_ml
    
    # Get material type and estimate weight
    material_type = analysis_result.get("material", "Plastic")
    weight = estimate_weight_from_ml(material_type)
    
    # Create footprint scan
    scan_data = {
        "waste_item_id": waste_item.id,
        "material_type": material_type,
        "estimated_weight_grams": weight,
        "ml_confidence_score": analysis_result.get("material_detection", {}).get("confidence", 0.0)
    }
    
    # Update footprint (trigger will handle monthly aggregation)
    from models import PlasticFootprintScan
    scan = PlasticFootprintScan(
        user_id=current_user.id,
        waste_item_id=waste_item.id,
        material_type=material_type,
        estimated_weight_grams=weight,
        ml_confidence_score=scan_data["ml_confidence_score"]
    )
    db.session.add(scan)
    db.session.commit()
```

### Step 2.5: Test API Endpoints
```bash
# Test footprint update
curl -X POST http://localhost:5000/api/footprint/scan/update-footprint \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "waste_item_id": 1,
    "material_type": "Plastic",
    "estimated_weight_grams": 25.5,
    "ml_confidence_score": 0.85
  }'

# Test dashboard
curl http://localhost:5000/api/footprint/dashboard \
  -H "Authorization: Bearer <token>"

# Test projects list
curl http://localhost:5000/api/projects/list
```

**✅ Completion Criteria:**
- All API endpoints respond correctly
- Database triggers fire properly
- Monthly aggregation works
- Badge levels calculated correctly

---

## 🌐 PHASE 3: WEB FRONTEND INTEGRATION (Day 6-8)

### Step 3.1: Install Dependencies
```bash
cd ReGenWorks-web  # or your web directory
npm install chart.js react-chartjs-2 lottie-web @react-google-maps/api react-speech-recognition i18next react-i18next
```

### Step 3.2: Create API Service Files
Create `src/services/api/footprintApi.js`:
```javascript
const API_BASE = '/api/footprint';

export const updateFootprint = async (scanData) => {
  const response = await fetch(`${API_BASE}/scan/update-footprint`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getToken()}`
    },
    body: JSON.stringify(scanData)
  });
  return response.json();
};

export const getFootprintDashboard = async (months = 6) => {
  const response = await fetch(`${API_BASE}/dashboard?months=${months}`, {
    headers: {
      'Authorization': `Bearer ${getToken()}`
    }
  });
  return response.json();
};
```

### Step 3.3: Create Footprint Dashboard Component
Create `src/components/FootprintTracker/FootprintDashboard.jsx`:
```jsx
import React, { useEffect, useState } from 'react';
import { getFootprintDashboard } from '../../services/api/footprintApi';
import MonthlyChart from './MonthlyChart';
import BadgeDisplay from './BadgeDisplay';

export default function FootprintDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const result = await getFootprintDashboard();
      if (result.success) {
        setData(result);
      }
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (!data) return <div>No data available</div>;

  return (
    <div className="footprint-dashboard">
      <BadgeDisplay badgeLevel={data.badge_level} />
      <MonthlyChart data={data.monthly_history} />
      {/* Recent scans list */}
    </div>
  );
}
```

### Step 3.4: Integrate with Existing Scan Flow
Update the scan result page to call footprint API:
```javascript
// After waste scan completes
if (user.isAuthenticated && result.material) {
  await updateFootprint({
    waste_item_id: wasteItem.id,
    material_type: result.material,
    estimated_weight_grams: estimatedWeight,
    ml_confidence_score: result.material_detection?.confidence || 0.0
  });
}
```

### Step 3.5: Add Navigation Links
Update `templates/base.html`:
```html
<nav>
  <a href="/footprint-dashboard">Plastic Footprint</a>
  <a href="/projects">Infrastructure Projects</a>
</nav>
```

### Step 3.6: Create Projects List Page
Create `templates/projects_list.html`:
```html
{% extends "base.html" %}
{% block content %}
<div id="projects-list"></div>
<script src="/static/js/projects.js"></script>
{% endblock %}
```

**✅ Completion Criteria:**
- Dashboard displays correctly
- Charts render with data
- API calls work
- Navigation links functional

---

## 📱 PHASE 4: ANDROID APP INTEGRATION (Day 9-12)

### Step 4.1: Project Setup
1. Create new Android project or update existing
2. Add dependencies to `build.gradle.kts`:
```kotlin
dependencies {
    implementation("com.github.PhilJay:MPAndroidChart:3.1.0")
    implementation("com.airbnb.android:lottie:6.1.0")
    implementation("org.tensorflow:tensorflow-lite:2.14.0")
    implementation("com.google.android.gms:play-services-maps:18.1.0")
    implementation("androidx.speech:speech:1.0.0")
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.google.firebase:firebase-firestore:24.7.0")
}
```

### Step 4.2: Create API Client
Create `ApiClient.kt`:
```kotlin
object ApiClient {
    private const val BASE_URL = "https://your-api-domain.com/api/"
    
    val retrofit: Retrofit = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
}
```

### Step 4.3: Create Footprint Dashboard Fragment
Create `FootprintDashboardFragment.kt`:
```kotlin
class FootprintDashboardFragment : Fragment() {
    private lateinit var chart: BarChart
    private lateinit var badgeView: BadgeDisplayView
    
    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        val view = inflater.inflate(R.layout.fragment_footprint_dashboard, container, false)
        chart = view.findViewById(R.id.monthlyChart)
        badgeView = view.findViewById(R.id.badgeView)
        loadDashboardData()
        return view
    }
    
    private fun loadDashboardData() {
        // Call API and update chart
    }
}
```

### Step 4.4: Integrate TFLite Model
Create `MaterialClassifier.kt`:
```kotlin
class MaterialClassifier(private val context: Context) {
    private var interpreter: Interpreter? = null
    
    init {
        loadModel()
    }
    
    private fun loadModel() {
        val modelFile = loadModelFile("waste_classifier.tflite")
        interpreter = Interpreter(modelFile)
    }
    
    fun classify(image: Bitmap): ClassificationResult {
        // Preprocess image
        val inputBuffer = preprocessImage(image)
        
        // Run inference
        val outputBuffer = ByteBuffer.allocateDirect(4 * 10) // 10 classes
        interpreter?.run(inputBuffer, outputBuffer)
        
        // Parse results
        return parseOutput(outputBuffer)
    }
}
```

### Step 4.5: Add Voice Input
Create `VoiceInputFragment.kt`:
```kotlin
class VoiceInputFragment : Fragment() {
    private lateinit var speechRecognizer: SpeechRecognizer
    
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        speechRecognizer = SpeechRecognizer.createSpeechRecognizer(requireContext())
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, getSelectedLanguage())
        }
        
        // Start listening
        speechRecognizer.startListening(intent)
    }
}
```

### Step 4.6: Create Localization Manager
Create `LocalizationManager.kt`:
```kotlin
object LocalizationManager {
    private val cache = mutableMapOf<String, Map<String, String>>()
    
    suspend fun loadStrings(language: String): Map<String, String> {
        if (cache.containsKey(language)) {
            return cache[language]!!
        }
        
        val strings = i18nApi.getStrings(language).await()
        cache[language] = strings
        return strings
    }
    
    fun getString(key: String, language: String = getCurrentLanguage()): String {
        return cache[language]?.get(key) ?: key
    }
}
```

**✅ Completion Criteria:**
- App builds and runs
- Dashboard displays data
- ML model loads and classifies
- Voice input works
- Localization switches correctly

---

## 🔥 PHASE 5: FIREBASE FIRESTORE SYNC (Day 13-14)

### Step 5.1: Initialize Firebase
```python
# firestore_sync.py
import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("path/to/serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()
```

### Step 5.2: Create Sync Function
```python
def sync_ledger_to_firestore(ledger_entry):
    """Sync ledger entry to Firestore"""
    project_ref = db.collection('ledger').document(ledger_entry.project_id)
    
    entry_data = {
        'timestamp': ledger_entry.timestamp.isoformat(),
        'status': ledger_entry.status,
        'verified_by': ledger_entry.verified_by,
        'batch_reference': ledger_entry.batch_reference,
        'block_hash': ledger_entry.block_hash,
        'previous_hash': ledger_entry.previous_hash,
        'data': ledger_entry.data
    }
    
    # Add to subcollection with timestamp as document ID
    project_ref.collection('entries').document(
        str(int(ledger_entry.timestamp.timestamp()))
    ).set(entry_data)
    
    # Mark as synced
    ledger_entry.firestore_synced = True
    db.session.commit()
```

### Step 5.3: Create Background Task
```python
from celery import Celery

celery = Celery('ReGenWorks')

@celery.task
def sync_ledger_async(ledger_id):
    ledger = ProjectLedger.query.get(ledger_id)
    if ledger and not ledger.firestore_synced:
        sync_ledger_to_firestore(ledger)
```

### Step 5.4: Integrate with Ledger Update
Update `api_definitions.py`:
```python
@projects_bp.route('/ledger/update', methods=['POST'])
@login_required
def update_ledger():
    # ... existing code ...
    
    # Queue async sync
    sync_ledger_async.delay(ledger.id)
    
    return jsonify({...})
```

**✅ Completion Criteria:**
- Firestore syncs correctly
- Entries are immutable
- Sync status tracked
- Background tasks work

---

## 🧪 PHASE 6: TESTING & VALIDATION (Day 15-16)

### Step 6.1: Unit Tests
```python
# tests/test_footprint.py
def test_badge_level_calculation():
    assert calculate_badge_level(1000) == 'Bronze'
    assert calculate_badge_level(3000) == 'Silver'
    assert calculate_badge_level(6000) == 'Gold'
    assert calculate_badge_level(12000) == 'Champion'
```

### Step 6.2: Integration Tests
```python
def test_footprint_update_flow():
    # Create scan
    # Verify monthly aggregation
    # Verify badge update
    # Verify trigger fired
```

### Step 6.3: End-to-End Tests
- Test complete scan → footprint → dashboard flow
- Test project creation → batch → ledger flow
- Test language switching → UI update flow

### Step 6.4: Performance Testing
- API response times
- Database query optimization
- Chart rendering performance
- ML model inference speed

**✅ Completion Criteria:**
- All tests pass
- Performance acceptable
- No regressions in existing features

---

## 📚 PHASE 7: DOCUMENTATION (Day 17)

### Step 7.1: API Documentation
- Document all new endpoints
- Include request/response examples
- Add authentication requirements

### Step 7.2: User Guides
- How to use footprint tracker
- How to view infrastructure projects
- How to change language
- How to use voice commands

### Step 7.3: Developer Documentation
- Architecture overview
- Database schema
- Component structure
- Integration patterns

**✅ Completion Criteria:**
- Documentation complete
- Examples provided
- Clear instructions

---

## 🚀 PHASE 8: DEPLOYMENT (Day 18-19)

### Step 8.1: Database Migration in Production
```bash
# Backup database first
pg_dump ReGenWorks > backup.sql

# Run migrations
psql -U postgres -d ReGenWorks < database_migrations.sql

# Verify
psql -U postgres -d ReGenWorks -c "\dt"
```

### Step 8.2: Deploy Backend
```bash
# Update requirements
pip freeze > requirements.txt

# Deploy to server
# (Follow your deployment process)
```

### Step 8.3: Deploy Web Frontend
```bash
npm run build
# Deploy dist/ folder
```

### Step 8.4: Release Android App
- Build release APK/AAB
- Test on devices
- Upload to Play Store (beta)

**✅ Completion Criteria:**
- All systems deployed
- No errors in production
- Monitoring in place

---

## 📊 MONITORING & MAINTENANCE

### Metrics to Track
- API response times
- Database query performance
- ML model accuracy
- User engagement (footprint scans, project views)
- Language usage statistics
- Error rates

### Regular Tasks
- Review and update weight lookup table
- Add new localization strings as needed
- Monitor Firestore sync status
- Update ML model as needed
- Review and optimize database queries

---

## 🎯 SUCCESS CRITERIA

1. ✅ All three features fully integrated
2. ✅ Database schema updated and tested
3. ✅ API endpoints functional
4. ✅ Web UI displays all features
5. ✅ Android app includes all features
6. ✅ Multilingual support working
7. ✅ Voice input functional
8. ✅ Infrastructure projects visible
9. ✅ Firestore sync operational
10. ✅ No breaking changes to existing features

---

## 🐛 TROUBLESHOOTING

### Common Issues

**Database trigger not firing:**
- Check trigger exists: `\d+ user_plastic_footprint_monthly`
- Verify function: `\df update_plastic_footprint_monthly`

**API returns 500 error:**
- Check logs for stack trace
- Verify database connection
- Check model imports

**ML model not loading:**
- Verify TFLite file in assets
- Check model input/output shapes
- Test with sample image

**Firestore sync failing:**
- Verify service account key
- Check network connectivity
- Review Firestore rules

---

This roadmap provides a structured approach to integrating all three features while maintaining code quality and system stability.

