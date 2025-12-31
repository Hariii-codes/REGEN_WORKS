# ReGenWorks Component Structure Plan
## Features: Plastic Footprint Tracker, Multilingual Support, Infrastructure Projects

---

## 📱 ANDROID APP STRUCTURE

### Project Structure
```
app/
├── src/
│   ├── main/
│   │   ├── java/com/ReGenWorks/
│   │   │   ├── MainActivity.kt
│   │   │   ├── models/
│   │   │   │   ├── User.kt
│   │   │   │   ├── WasteItem.kt
│   │   │   │   ├── PlasticFootprintScan.kt
│   │   │   │   ├── InfrastructureProject.kt
│   │   │   │   └── LocalizationString.kt
│   │   │   ├── ui/
│   │   │   │   ├── footprint/
│   │   │   │   │   ├── FootprintDashboardFragment.kt
│   │   │   │   │   ├── FootprintChartView.kt
│   │   │   │   │   └── BadgeDisplayView.kt
│   │   │   │   ├── projects/
│   │   │   │   │   ├── ProjectsListFragment.kt
│   │   │   │   │   ├── ProjectDetailFragment.kt
│   │   │   │   │   └── ProjectMapView.kt
│   │   │   │   ├── scan/
│   │   │   │   │   ├── ScanFragment.kt
│   │   │   │   │   ├── MaterialSelectionDialog.kt
│   │   │   │   │   └── WeightEstimationView.kt
│   │   │   │   ├── voice/
│   │   │   │   │   ├── VoiceInputFragment.kt
│   │   │   │   │   └── VoiceCommandProcessor.kt
│   │   │   │   └── onboarding/
│   │   │   │       ├── OnboardingActivity.kt
│   │   │   │       └── OnboardingStepFragment.kt
│   │   │   ├── network/
│   │   │   │   ├── ApiClient.kt
│   │   │   │   ├── FootprintApi.kt
│   │   │   │   ├── ProjectsApi.kt
│   │   │   │   └── I18nApi.kt
│   │   │   ├── ml/
│   │   │   │   ├── TFLiteModelLoader.kt
│   │   │   │   ├── MaterialClassifier.kt
│   │   │   │   └── WeightEstimator.kt
│   │   │   ├── localization/
│   │   │   │   ├── LocalizationManager.kt
│   │   │   │   ├── StringResourceLoader.kt
│   │   │   │   └── LanguagePreferenceManager.kt
│   │   │   ├── firebase/
│   │   │   │   ├── FirestoreSync.kt
│   │   │   │   └── LedgerSyncService.kt
│   │   │   └── utils/
│   │   │       ├── IconHelper.kt
│   │   │       └── OfflineManager.kt
│   │   ├── res/
│   │   │   ├── layout/
│   │   │   │   ├── fragment_footprint_dashboard.xml
│   │   │   │   ├── fragment_projects_list.xml
│   │   │   │   ├── fragment_scan.xml
│   │   │   │   ├── item_project_card.xml
│   │   │   │   └── view_badge_display.xml
│   │   │   ├── values/
│   │   │   │   ├── strings.xml (English)
│   │   │   │   ├── strings-hi.xml (Hindi)
│   │   │   │   ├── strings-kn.xml (Kannada)
│   │   │   │   ├── strings-ta.xml (Tamil)
│   │   │   │   └── strings-mr.xml (Marathi)
│   │   │   ├── drawable/
│   │   │   │   ├── ic_scan.xml
│   │   │   │   ├── ic_drop_points.xml
│   │   │   │   ├── ic_dashboard.xml
│   │   │   │   ├── ic_rewards.xml
│   │   │   │   └── badge_bronze.xml, badge_silver.xml, etc.
│   │   │   └── raw/
│   │   │       ├── waste_classifier.tflite
│   │   │       └── weight_lookup.json
│   │   └── assets/
│   │       └── lottie/
│   │           ├── scan_animation.json
│   │           ├── drop_points_animation.json
│   │           └── onboarding_tutorial.json
│   └── test/
└── build.gradle.kts
```

### Key Android Components

#### 1. Plastic Footprint Tracker
- **FootprintDashboardFragment.kt**
  - Displays monthly bar chart using MPAndroidChart
  - Shows badge level (Bronze/Silver/Gold/Champion)
  - Progress indicators and comparison percentages
  - Recent scans list

- **FootprintChartView.kt**
  - Custom view using MPAndroidChart library
  - Bar chart for monthly weight data
  - Line chart overlay for comparison trends

- **BadgeDisplayView.kt**
  - Circular progress indicator
  - Badge icon (Bronze/Silver/Gold/Champion)
  - Badge level text

- **MaterialSelectionDialog.kt**
  - Shown when ML confidence < threshold
  - Icon-based material selection
  - Voice input option

#### 2. Multilingual & Low-Literacy Support
- **LocalizationManager.kt**
  - Loads strings from API or local cache
  - Handles language switching
  - Caches strings for offline use

- **VoiceInputFragment.kt**
  - Uses Android SpeechRecognizer API
  - Voice command processing
  - Visual feedback during recording

- **OnboardingActivity.kt**
  - Lottie animations for UI explanation
  - Voice-guided tutorial
  - Icon-first navigation

- **IconHelper.kt**
  - Manages Lottie animations
  - Icon resource loading
  - Simple labeled icons for low-literacy users

#### 3. Infrastructure Projects
- **ProjectsListFragment.kt**
  - RecyclerView with project cards
  - Status badges (planned/in-progress/completed)
  - Filter by status
  - Top contributor badges

- **ProjectDetailFragment.kt**
  - Project details with map preview
  - Contribution amount display
  - Ledger entries list
  - Progress bar

- **ProjectMapView.kt**
  - Google Maps integration
  - Project location markers
  - User contribution visualization

#### 4. ML Integration
- **TFLiteModelLoader.kt**
  - Loads waste classification model
  - Model version management

- **MaterialClassifier.kt**
  - Image preprocessing
  - Model inference
  - Confidence score calculation

- **WeightEstimator.kt**
  - Material type → weight lookup
  - Average weight calculation
  - Confidence threshold checking

---

## 🌐 WEB APP STRUCTURE

### Project Structure
```
ReGenWorks-web/
├── src/
│   ├── components/
│   │   ├── FootprintTracker/
│   │   │   ├── FootprintDashboard.jsx
│   │   │   ├── MonthlyChart.jsx (Chart.js)
│   │   │   ├── BadgeDisplay.jsx
│   │   │   └── RecentScans.jsx
│   │   ├── Projects/
│   │   │   ├── ProjectsList.jsx
│   │   │   ├── ProjectCard.jsx
│   │   │   ├── ProjectDetail.jsx
│   │   │   └── ProjectMap.jsx (Google Maps API)
│   │   ├── VoiceInput/
│   │   │   ├── VoiceRecorder.jsx (Web Speech API)
│   │   │   └── VoiceCommandHandler.jsx
│   │   ├── Localization/
│   │   │   ├── LanguageSelector.jsx
│   │   │   └── LocalizedText.jsx
│   │   └── Icons/
│   │       ├── ScanIcon.jsx (Lottie)
│   │       ├── DropPointsIcon.jsx
│   │       └── DashboardIcon.jsx
│   ├── services/
│   │   ├── api/
│   │   │   ├── footprintApi.js
│   │   │   ├── projectsApi.js
│   │   │   └── i18nApi.js
│   │   ├── ml/
│   │   │   └── materialClassifier.js
│   │   └── firebase/
│   │       └── firestoreSync.js
│   ├── hooks/
│   │   ├── useLocalization.js
│   │   ├── useVoiceInput.js
│   │   └── useOfflineSync.js
│   ├── utils/
│   │   ├── weightLookup.js
│   │   └── iconHelper.js
│   ├── locales/
│   │   ├── en.json
│   │   ├── hi.json
│   │   ├── kn.json
│   │   ├── ta.json
│   │   └── mr.json
│   └── App.jsx
└── public/
    └── lottie/
        ├── scan.json
        └── drop_points.json
```

### Key Web Components

#### 1. Plastic Footprint Tracker
- **FootprintDashboard.jsx**
  - Main dashboard container
  - Fetches data from `/api/footprint/dashboard`
  - Responsive grid layout

- **MonthlyChart.jsx**
  - Uses Chart.js library
  - Bar chart for monthly weights
  - Tooltip with comparison percentage

- **BadgeDisplay.jsx**
  - Badge level visualization
  - Progress ring
  - Badge icon (SVG or image)

#### 2. Multilingual Support
- **LanguageSelector.jsx**
  - Dropdown for language selection
  - Saves preference to user profile
  - Fetches strings from `/api/i18n/strings`

- **LocalizedText.jsx**
  - Wrapper component for localized strings
  - Fallback to English if translation missing
  - Context-aware (web/android)

- **VoiceRecorder.jsx**
  - Web Speech API integration
  - Voice command recognition
  - Visual feedback (waveform animation)

#### 3. Infrastructure Projects
- **ProjectsList.jsx**
  - Grid/List view toggle
  - Filter by status
  - Pagination
  - Fetches from `/api/projects/list`

- **ProjectCard.jsx**
  - Project preview card
  - Status badge
  - Map thumbnail
  - Contribution amount
  - Top contributor badge

- **ProjectMap.jsx**
  - Google Maps API integration
  - Project location markers
  - Info windows with project details

---

## 🔧 BACKEND STRUCTURE

### New Files
```
ReGenWorks-backend/
├── api_definitions.py (already created)
├── footprint_service.py
├── projects_service.py
├── i18n_service.py
├── ml_integration.py
└── firestore_sync.py
```

### Service Modules

#### footprint_service.py
```python
def estimate_weight_from_ml(material_type, category, confidence_score):
    """Lookup weight from material_weight_lookup table"""
    
def update_monthly_footprint(user_id, weight_grams):
    """Update or create monthly footprint record"""
    
def calculate_badge_level(total_weight_grams):
    """Calculate badge level based on weight thresholds"""
    
def get_footprint_dashboard_data(user_id, months=6):
    """Aggregate dashboard data"""
```

#### projects_service.py
```python
def create_waste_batch(total_weight, material_type, project_id, waste_item_ids):
    """Create batch and link contributors"""
    
def update_project_ledger(project_id, status, verified_by, batch_reference):
    """Create immutable ledger entry"""
    
def calculate_top_contributors(project_id):
    """Identify top 10% contributors"""
    
def sync_ledger_to_firestore(ledger_entry):
    """Sync to Firebase Firestore"""
```

#### i18n_service.py
```python
def get_localized_strings(language, context='both', keys=None):
    """Fetch localized strings from database"""
    
def cache_strings_for_offline(language):
    """Preload strings for offline use"""
```

#### ml_integration.py
```python
def classify_waste_material(image_path, tflite_model_path):
    """Run TFLite model inference"""
    
def get_weight_estimate(material_type, category, confidence):
    """Get weight from lookup table"""
    
def check_confidence_threshold(confidence, material_type):
    """Check if confidence meets threshold for auto-selection"""
```

---

## 🎨 UI PATTERNS

### Icon-First Design (Low-Literacy)
- **Primary Actions**: Large Lottie icons with simple labels
- **Navigation**: Bottom navigation with icons only
- **Onboarding**: Animated tutorial with voice guidance
- **Color Coding**: Status colors (green=good, yellow=warning, red=error)

### Multilingual UI
- **Language Switcher**: Top-right dropdown
- **RTL Support**: For languages that require it
- **Font Loading**: Custom fonts for regional languages
- **Voice Commands**: Language-specific command recognition

### Dashboard Layout
- **Mobile**: Single column, scrollable
- **Tablet**: Two-column grid
- **Desktop**: Three-column grid with sidebar

---

## 📊 DATA FLOW

### Plastic Footprint Flow
1. User scans waste → ML classifies material
2. If confidence < threshold → Show material selection dialog
3. Weight estimated from lookup table
4. POST `/api/footprint/scan/update-footprint`
5. Trigger updates `user_plastic_footprint_monthly`
6. Badge level calculated and updated
7. Dashboard refreshes with new data

### Infrastructure Project Flow
1. Municipality creates batch → POST `/api/projects/batch/create`
2. Waste items linked to batch
3. Contributors calculated
4. Project allocated weight updated
5. Ledger entry created → POST `/api/projects/ledger/update`
6. Ledger synced to Firestore (async)
7. Users see updated project status

### Multilingual Flow
1. User selects language → POST `/api/i18n/user/preferences`
2. Frontend fetches strings → GET `/api/i18n/strings?language=hi`
3. Strings cached locally
4. UI updates with localized text
5. Voice commands use selected language

---

## 🔐 SECURITY & OFFLINE SUPPORT

### Offline-First Architecture
- **Local Storage**: Cache strings, recent scans, project data
- **Sync Queue**: Queue API calls when offline
- **Service Worker** (Web): Background sync
- **WorkManager** (Android): Background sync tasks

### Security
- **Authentication**: JWT tokens for API access
- **Rate Limiting**: Prevent abuse
- **Input Validation**: Sanitize all inputs
- **CORS**: Configured for web app domain

---

## 📦 DEPENDENCIES

### Android
```gradle
dependencies {
    // Charts
    implementation 'com.github.PhilJay:MPAndroidChart:v3.1.0'
    
    // Lottie animations
    implementation 'com.airbnb.android:lottie:6.1.0'
    
    // ML
    implementation 'org.tensorflow:tensorflow-lite:2.14.0'
    
    // Maps
    implementation 'com.google.android.gms:play-services-maps:18.1.0'
    
    // Speech Recognition
    implementation 'androidx.speech:speech:1.0.0'
    
    // Networking
    implementation 'com.squareup.retrofit2:retrofit:2.9.0'
    implementation 'com.squareup.okhttp3:okhttp:4.11.0'
    
    // Firebase
    implementation 'com.google.firebase:firebase-firestore:24.7.0'
}
```

### Web
```json
{
  "dependencies": {
    "chart.js": "^4.4.0",
    "lottie-web": "^5.12.2",
    "@react-google-maps/api": "^2.19.0",
    "react-speech-recognition": "^3.10.0",
    "i18next": "^23.5.1",
    "react-i18next": "^13.2.2"
  }
}
```

---

## 🧪 TESTING STRATEGY

### Unit Tests
- ML model inference accuracy
- Weight estimation logic
- Badge level calculation
- Localization string loading

### Integration Tests
- API endpoint responses
- Database triggers
- Firestore sync
- Offline sync queue

### UI Tests
- Voice command recognition
- Chart rendering
- Map interactions
- Language switching

---

This structure maintains modularity, follows existing patterns, and supports all three new features while preserving backward compatibility.

