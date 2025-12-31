"""
Helper functions for localization in templates
Uses JSON files as primary source, database as fallback
"""

from flask import current_app, g, session
from flask_login import current_user
import json
from pathlib import Path

# Cache for loaded JSON translations
_json_translation_cache = {}

def _load_json_translations(language='en'):
    """Load translations from JSON file"""
    if language in _json_translation_cache:
        return _json_translation_cache[language]
    
    # Try src/locales first, then locales
    src_locales_dir = Path('src/locales')
    locales_dir = Path('locales')
    
    if src_locales_dir.exists():
        translation_file = src_locales_dir / f'{language}.json'
    else:
        translation_file = locales_dir / f'{language}.json'
    
    if not translation_file.exists():
        # Fallback to English
        if language != 'en':
            return _load_json_translations('en')
        return {}
    
    try:
        with open(translation_file, 'r', encoding='utf-8') as f:
            translations = json.load(f)
            _json_translation_cache[language] = translations
            return translations
    except Exception:
        return {}

def get_localized_string(key, language=None, default=None):
    """
    Get localized string from JSON files (primary) or database (fallback)
    
    Args:
        key: String key (e.g., 'nav.scan')
        language: Language code (defaults to user's preferred language)
        default: Default value if not found
    
    Returns:
        Localized string or default
    """
    if language is None:
        # Check session first (for immediate updates), then user preference
        if 'language' in session:
            language = session['language']
        elif hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            language = getattr(current_user, 'preferred_language', 'en') or 'en'
        else:
            language = 'en'
    
    # Try to get from cache first (stored in g)
    cache_key = f"loc_{key}_{language}"
    if hasattr(g, cache_key):
        return getattr(g, cache_key)
    
    # Try JSON files first
    translations = _load_json_translations(language)
    if key in translations:
        value = translations[key]
        setattr(g, cache_key, value)
        return value
    
    # Fallback to English JSON
    if language != 'en':
        en_translations = _load_json_translations('en')
        if key in en_translations:
            value = en_translations[key]
            setattr(g, cache_key, value)
            return value
    
    # Fallback to database (for backward compatibility)
    try:
        from models import LocalizationString
        loc_string = LocalizationString.query.filter_by(
            key=key,
            language=language
        ).first()
        
        if loc_string:
            value = loc_string.value
        else:
            # Fallback to English in database
            if language != 'en':
                loc_string = LocalizationString.query.filter_by(
                    key=key,
                    language='en'
                ).first()
                value = loc_string.value if loc_string else (default or key)
            else:
                value = default or key
        
        # Cache in g
        setattr(g, cache_key, value)
        return value
    except Exception:
        return default or key

def get_current_language():
    """
    Get current language from session or user preference
    """
    from flask_login import current_user
    from flask import session
    
    # Check session first (for immediate updates)
    if 'language' in session:
        return session['language']
    
    # Check user preference if authenticated
    try:
        if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            lang = getattr(current_user, 'preferred_language', None)
            if lang:
                # Also set in session for consistency
                session['language'] = lang
                return lang
    except Exception:
        pass
    
    # Default to English
    return 'en'

# Make function available to templates
def init_app(app):
    """Register helper function with Flask app"""
    from localization_manager import get_all_languages
    app.jinja_env.globals['get_localized_string'] = get_localized_string
    app.jinja_env.globals['get_all_languages'] = get_all_languages
    app.jinja_env.globals['get_current_language'] = get_current_language

