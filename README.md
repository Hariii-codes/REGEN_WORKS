# ReGenWorks

A cutting-edge waste management platform that transforms recycling into an engaging, rewarding experience through advanced AI technologies, multilingual support, and user-centric design.

## 🌟 Key Features

### Core Features
- **AI-powered Material Identification**: Upload images of waste items to receive detailed analysis on recyclability, material composition, and proper disposal methods using Google Gemini AI
- **Blockchain-enabled Waste Tracking**: Monitor waste items from drop-off to recycling completion with a secure, transparent tracking system
- **Smart Recycling Guidance**: Get personalized instructions on how to properly prepare and recycle different types of materials
- **Interactive Drop-off Map**: Find nearby recycling centers and drop-off points with an interactive map
- **Infrastructure Reporting**: Report damaged waste management infrastructure through webcam photos
- **Community Marketplace**: List recyclable items for reuse in the community marketplace
- **Municipality Integration**: Direct routing of recyclable materials to municipal collection services
- **Gamification & Rewards**: Earn eco-points and achievements for responsible waste management

### Advanced Features
- **Plastic Footprint Tracker**: Track plastic waste like a fitness tracker with monthly aggregation, badges, and progress visualization
- **Multilingual Support**: Full support for 6 languages (English, Hindi, Kannada, Tamil, Marathi, Bengali) with voice input capabilities
- **Low-Literacy Support**: Icon-first UI design for users with varying literacy levels
- **Infrastructure Project Feedback Loop**: Blockchain transparency for waste contributions to infrastructure projects
- **Carbon Emissions Calculator**: Track and visualize carbon footprint reduction from recycling efforts

## 🛠️ Technical Stack

- **Backend**: Flask (Python 3.11+)
- **Database**: PostgreSQL (with SQLite for development)
- **AI/ML**: Google Gemini 2.0 Flash API, OpenCV, scikit-learn
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Authentication**: Flask-Login, Flask-Bcrypt
- **Forms**: Flask-WTF, WTForms
- **Image Processing**: Pillow (PIL), OpenCV
- **Geospatial**: OpenLayers for maps
- **Localization**: JSON-based i18n system with Gemini AI translations

## 🚀 Getting Started

### Prerequisites

- Python 3.9+ (3.11 recommended)
- PostgreSQL (or SQLite for development)
- pip (Python package manager)
- Google Gemini API key (for AI features)

### Local Development Setup

#### 1. Clone the repository
```bash
git clone https://github.com/yourusername/regenworks.git
cd regenworks
```

#### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

#### 3. Install dependencies
```bash
pip install -r dependencies.txt
# Or if using requirements-render.txt
pip install -r requirements-render.txt
```

#### 4. Set up PostgreSQL
- Install PostgreSQL if you haven't already
- **For Windows**: Use the PowerShell setup script:
  ```powershell
  .\setup_postgresql.ps1
  ```
- **For Linux/Mac**: Use the bash setup script:
  ```bash
  chmod +x setup_database.sh
  ./setup_database.sh
  ```
- **Manual Setup**: See [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md) for detailed instructions
- Or create database manually:
  ```bash
  createdb regenworks
  ```

#### 5. Configure environment variables
Copy the example environment file and fill in your values:
```bash
# On Windows
copy .env.example .env

# On Linux/Mac
cp .env.example .env
```

Then edit `.env` and fill in your actual values:
- `DATABASE_URL` - Database connection string (SQLite or PostgreSQL)
  - **PostgreSQL format**: `postgresql://username:password@host:port/database_name`
  - **Example**: `postgresql://postgres:mypassword@localhost:5432/regenworks`
  - See [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md) for detailed setup instructions
- `SESSION_SECRET` - Flask session secret (generate with: `python -c "import secrets; print(secrets.token_hex(32))"`)
- `GEMINI_API_KEY` - Google Gemini API key (required)
- `FIREBASE_SERVICE_ACCOUNT_JSON` - Firebase JSON (optional, for cloud deployments)
- `FIREBASE_SERVICE_ACCOUNT_KEY` - Firebase file path (optional, for local development)
- `GOOGLE_MAPS_API_KEY` - Google Maps API key (optional)

See `.env.example` for all available environment variables and detailed comments.

#### 6. Initialize the database
```bash
# For fresh database setup
python recreate_db.py

# For database migrations (if upgrading)
python migrate_new_features.py

# Or run SQL migrations directly
psql -U postgres -d regenworks < database_migrations.sql
```

#### 7. Seed localization data (optional)
```bash
python seed_all_languages.py
```

#### 8. Run the application
```bash
python main.py
```
The application will be available at http://localhost:5000

### Using Docker (Alternative)

If you prefer using Docker:

```bash
# Build the Docker image
docker build -t regenworks .

# Run the container
docker run -p 5000:5000 --env-file .env regenworks
```

## 🗃️ Database Schema

The application uses several related models:

### Core Models
- **User**: Authentication, profile, gamification data, language preferences
- **WasteItem**: Uploaded waste items with AI analysis results
- **DropLocation**: Recycling centers and drop-off points
- **WasteJourneyBlock**: Blockchain-like tracking for waste journey
- **Achievement**: Gamification achievements and badges
- **Reward**: Points and rewards for user actions
- **InfrastructureReport**: Citizen reports of damaged infrastructure

### Feature Models
- **UserPlasticFootprintMonthly**: Monthly aggregated plastic footprint data
- **PlasticFootprintScan**: Individual scan records for footprint tracking
- **MaterialWeightLookup**: ML weight estimation lookup table
- **LocalizationString**: UI strings for multilingual support
- **InfrastructureProject**: Infrastructure project details
- **WasteBatch**: Collected waste batches for projects
- **ProjectContributor**: User contributions to infrastructure projects
- **ProjectLedger**: Blockchain-like immutable ledger for projects

## 📊 API Endpoints

### Main Routes
- `/`: Home page and waste item upload/analysis
- `/auth/register`: User registration
- `/auth/login`: User login
- `/auth/profile`: User profile and statistics
- `/marketplace`: Community marketplace for recyclable items
- `/municipality`: Items routed to municipal collection
- `/drop-points`: Map of recycling drop-off locations
- `/tracking`: Blockchain-based waste journey tracking
- `/infrastructure`: Infrastructure reporting system

### Feature-Specific API Endpoints

#### Plastic Footprint Tracker
- `POST /api/footprint/scan/update-footprint` - Update footprint on scan
- `GET /api/footprint/dashboard` - Get dashboard data
- `GET /api/footprint/weight-lookup` - Get weight lookup table

#### Multilingual Support
- `GET /api/i18n/strings` - Get localized strings
- `GET /api/i18n/user/preferences` - Get user preferences
- `POST /api/i18n/user/preferences` - Update user preferences
- `POST /api/i18n/voice/process` - Process voice commands

#### Infrastructure Projects
- `GET /api/projects/list` - List all projects
- `GET /api/projects/{project_id}` - Get project details
- `POST /api/projects/batch/create` - Create waste batch
- `POST /api/projects/ledger/update` - Update project ledger

## 🎨 UI Features

### Multilingual Support
- **6 Languages**: English, Hindi, Kannada, Tamil, Marathi, Bengali
- **Voice Input**: Speech-to-text for low-literacy users
- **Icon-First Design**: Visual navigation for all literacy levels
- **Dynamic Language Switching**: Real-time UI translation

### Plastic Footprint Dashboard
- Monthly aggregation with comparison percentages
- Badge levels: Bronze, Silver, Gold, Champion
- Interactive charts and visualizations
- Recent scans history

### Infrastructure Projects
- Project listing with status badges
- Google Maps integration
- Contribution tracking
- Top contributor badges (top 10%)
- Blockchain-like ledger transparency
- Project progress visualization

## 🚀 Deployment

### Deploy to Railway

ReGenWorks can be easily deployed to Railway. See [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) for detailed instructions.

**Quick Setup:**
1. Create a new project on Railway
2. Connect your GitHub repository
3. Set the following environment variables:
   - `DATABASE_URL=sqlite:///data.db` (or PostgreSQL connection string)
   - `GEMINI_API_KEY=your_gemini_api_key`
   - `FIREBASE_SERVICE_ACCOUNT_JSON={your_firebase_json}` (optional)
   - `SESSION_SECRET=your_random_secret_key`
4. Railway will automatically deploy your application

For complete setup instructions, see [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md).

### Deploy to Render.com

This application is configured for easy deployment on Render.com:

1. Fork or clone this repository to your GitHub account
2. Sign up for Render.com and connect your GitHub account
3. Create a new Web Service and select your repository
4. Use the following settings:
   - Environment: Python
   - Build Command: `pip install -r requirements-render.txt`
   - Start Command: `gunicorn --bind 0.0.0.0:$PORT --workers=2 main:app`

5. Add the following environment variables:
   - `SESSION_SECRET`: Generate a secure random string
   - `FLASK_ENV`: production
   - `PYTHONUNBUFFERED`: true
   - `PYTHON_VERSION`: 3.11.8
   - `GEMINI_API_KEY`: Your Google Gemini API key

6. Create a PostgreSQL database in Render:
   - Go to Dashboard → New → PostgreSQL
   - Link it to your web service (Render will automatically set the DATABASE_URL environment variable)

7. Deploy your application
   - The application will automatically set up the database schema during the first deployment
   - If needed, you can run database migrations through the Render shell

### Database Management

For database schema updates after deployment:

```bash
# For adding new columns to existing tables:
python update_db.py

# For completely resetting the database (warning: all data will be lost):
python recreate_db.py

# For running feature migrations:
python migrate_new_features.py
```

## 🔐 Security & Performance

### Security
- JWT authentication for API endpoints
- Input validation and sanitization
- SQL injection prevention (SQLAlchemy ORM)
- CORS configuration for web app
- Password hashing with Flask-Bcrypt
- Session management with Flask-Login

### Performance
- Database indexes on frequently queried columns
- Caching for localization strings
- Async Firestore sync (background tasks)
- Offline-first architecture
- Image optimization and compression

### Offline Support
- Local string caching
- Offline scan queue
- Service Worker (Web) / WorkManager (Android)
- Background sync when online

## 📝 Project Structure

```
regenworks/
├── app.py                 # Flask application initialization
├── main.py                # Application entry point
├── models.py              # Database models
├── routes.py              # Main application routes
├── auth.py                # Authentication routes
├── gemini_service.py      # AI analysis service
├── material_detection.py # Material detection ML
├── carbon_calculator.py   # Carbon footprint calculator
├── rewards.py             # Gamification system
├── tracking.py            # Waste tracking routes
├── infrastructure.py      # Infrastructure reporting routes
├── new_features_routes.py # Feature-specific routes
├── api_definitions.py     # REST API endpoints
├── localization_helper.py # i18n helper functions
├── database_migrations.sql # Database schema
├── templates/             # HTML templates
├── static/               # Static files (CSS, JS, images)
├── locales/              # Localization JSON files
└── docs/                 # Documentation
```

## 🧪 Testing

### Manual Testing Checklist

#### Database
- [ ] All tables created
- [ ] Triggers fire correctly
- [ ] Indexes created
- [ ] Seed data loaded

#### API Endpoints
- [ ] POST /api/footprint/scan/update-footprint
- [ ] GET /api/footprint/dashboard
- [ ] GET /api/i18n/strings
- [ ] POST /api/i18n/user/preferences
- [ ] GET /api/projects/list
- [ ] GET /api/projects/{id}
- [ ] POST /api/projects/batch/create

#### Frontend
- [ ] Dashboard displays data
- [ ] Charts render correctly
- [ ] Language switching works
- [ ] Voice input functional
- [ ] Projects list displays
- [ ] Map integration works
- [ ] AI analysis works correctly

#### Integration
- [ ] Scan flow updates footprint
- [ ] Monthly aggregation works
- [ ] Badge levels update
- [ ] No breaking changes

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open issues for bugs and feature requests.

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add some amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Write clear commit messages
- Add comments for complex logic
- Update documentation for new features
- Test your changes before submitting

## 📚 Documentation

- **Implementation Summary**: See `IMPLEMENTATION_SUMMARY.md`
- **Database Schema**: See `database_migrations.sql`
- **API Documentation**: See `api_definitions.py` (inline docstrings)
- **Component Structure**: See `COMPONENT_STRUCTURE.md`
- **Integration Guide**: See `INTEGRATION_ROADMAP.md`
- **Multilingual Features**: See `MULTILINGUAL_IMPLEMENTATION.md`

## 🐛 Known Issues & Considerations

1. **TFLite Model**: Requires waste classification model file for offline material detection
2. **Firebase Setup**: Requires Firebase project and service account key for blockchain ledger sync
3. **Google Maps API**: Requires API key for map features
4. **ML Confidence Threshold**: May need tuning based on model accuracy
5. **Weight Lookup**: May need expansion based on real-world data
6. **Gemini API**: Requires valid API key and may have rate limits

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 Contact & Support

- **Project Link**: [https://github.com/yourusername/regenworks](https://github.com/tether007/regenworks)
- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Documentation**: Check the `docs/` folder and markdown files for detailed documentation

## 🙏 Acknowledgments

- Google Gemini AI for waste analysis
- OpenCV community for computer vision tools
- Flask community for the excellent web framework
- All contributors and users of ReGenWorks

---

**Made with ❤️ for a cleaner planet**
