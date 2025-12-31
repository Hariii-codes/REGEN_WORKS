import os
from dotenv import load_dotenv
from app import app
from routes import register_routes
from auth import auth_bp

# Load environment variables from .env file
load_dotenv()

# Configure the upload folder
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Register auth blueprint
app.register_blueprint(auth_bp)

# Register API routes for new features
from api_definitions import register_api_routes
register_api_routes(app)

# Register infrastructure project routes
from infrastructure_projects import register_infrastructure_project_routes
register_infrastructure_project_routes(app)

# Register all routes (this includes new feature routes)
register_routes(app)

# Initialize localization helper
from localization_helper import init_app
init_app(app)

# Global error handler for better debugging
@app.errorhandler(Exception)
def handle_all_exceptions(e):
    """Global exception handler to catch all unhandled exceptions"""
    import traceback
    import logging
    from flask import request, jsonify, render_template
    
    logger = logging.getLogger(__name__)
    error_msg = str(e) if e else "An unexpected error occurred"
    
    # Log the full traceback
    logger.error(f"Unhandled exception in {request.endpoint or 'unknown'}: {error_msg}")
    logger.error(f"Request path: {request.path}")
    logger.error(f"Request method: {request.method}")
    logger.error(f"Traceback:\n{traceback.format_exc()}")
    
    # Return JSON for API routes, HTML for web routes
    if request.path.startswith('/api/'):
        return jsonify({
            'error': 'Internal server error',
            'message': error_msg,
            'path': request.path
        }), 500
    
    # For web routes, show error page
    return render_template("error.html", error="Server error"), 500

# Health check endpoint for deployment monitoring
@app.route('/health')
def health_check():
    """Health check endpoint to verify database and app status"""
    from flask import jsonify
    from sqlalchemy import inspect
    from app import db
    from models import User
    
    status = {
        'status': 'ok',
        'database': 'unknown',
        'tables': [],
        'user_table_exists': False
    }
    
    try:
        # Check database connection
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        status['tables'] = existing_tables
        status['database'] = 'connected'
        
        # Check if User table exists
        existing_tables_lower = [t.lower() for t in existing_tables]
        if 'user' in existing_tables_lower:
            status['user_table_exists'] = True
            # Try to query the table
            try:
                user_count = User.query.count()
                status['user_count'] = user_count
            except Exception as e:
                status['user_query_error'] = str(e)
        else:
            status['user_table_exists'] = False
            status['warning'] = 'User table does not exist. Registration will fail.'
            
    except Exception as e:
        status['status'] = 'error'
        status['database'] = 'disconnected'
        status['error'] = str(e)
    
    return jsonify(status), 200 if status['status'] == 'ok' else 500

# Check if user needs language selection on first visit
@app.before_request
def check_language_selection():
    from flask_login import current_user
    from flask import request, redirect, url_for
    
    # Skip for static files, auth routes, API routes, and language selection itself
    if (request.endpoint and 
        not request.endpoint.startswith('static') and
        not request.endpoint.startswith('auth.') and
        'api' not in request.endpoint and
        request.endpoint != 'select_language' and
        hasattr(current_user, 'is_authenticated') and
        current_user.is_authenticated and
        not getattr(current_user, 'onboarding_completed', False)):
        # Redirect to language selection if not completed
        return redirect(url_for('select_language'))

if __name__ == "__main__":
    # Determine if we're running in production or development
    is_prod = os.environ.get('FLASK_ENV') == 'production'
    port = int(os.environ.get('PORT', 5000))
    
import os

is_prod = os.environ.get("RENDER") is not None
port = int(os.environ.get("PORT", 10000))

app.run(
    host="0.0.0.0",
    port=port,
    debug=not is_prod
)