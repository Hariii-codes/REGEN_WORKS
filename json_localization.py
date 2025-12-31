"""
JSON-based localization system
Loads translations from JSON files instead of database
"""
import json
import os
from pathlib import Path
from flask import session, g

# Cache for loaded translations
_translation_cache = {}

def load_translations(language='en'):
    """Load translations for a language from JSON file"""
    if language in _translation_cache:
        return _translation_cache[language]
    
    locales_dir = Path('locales')
    translation_file = locales_dir / f'{language}.json'
    
    if not translation_file.exists():
        # Fallback to English
        if language != 'en':
            return load_translations('en')
        return {}
    
    try:
        with open(translation_file, 'r', encoding='utf-8') as f:
            translations = json.load(f)
            _translation_cache[language] = translations
            return translations
    except Exception as e:
        print(f"Error loading translations for {language}: {e}")
        if language != 'en':
            return load_translations('en')
        return {}

def get_translation(key, language=None, default=None):
    """
    Get translation for a key
    
    Args:
        key: Translation key (e.g., 'nav.analyze')
        language: Language code (defaults to current language)
        default: Default value if translation not found
    
    Returns:
        Translated string or default
    """
    from flask_login import current_user
    
    # Determine language
    if language is None:
        # Check session first (for immediate updates)
        if 'language' in session:
            language = session['language']
        elif hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            language = getattr(current_user, 'preferred_language', 'en') or 'en'
        else:
            language = 'en'
    
    # Load translations
    translations = load_translations(language)
    
    # Get translation
    if key in translations:
        return translations[key]
    
    # Fallback to English if not current language
    if language != 'en':
        en_translations = load_translations('en')
        if key in en_translations:
            return en_translations[key]
    
    # Return default or key
    return default or key

def get_current_language():
    """Get current language from session or user preference"""
    from flask_login import current_user
    
    if 'language' in session:
        return session['language']
    elif hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
        return getattr(current_user, 'preferred_language', 'en') or 'en'
    else:
        return 'en'

def get_available_languages():
    """Get list of available languages"""
    locales_dir = Path('locales')
    languages = []
    
    # Language metadata
    lang_metadata = {
        'en': {'name': 'English', 'native': 'English'},
        'hi': {'name': 'Hindi', 'native': 'हिन्दी'},
        'kn': {'name': 'Kannada', 'native': 'ಕನ್ನಡ'},
        'ta': {'name': 'Tamil', 'native': 'தமிழ்'},
        'mr': {'name': 'Marathi', 'native': 'मराठी'},
        'bn': {'name': 'Bengali', 'native': 'বাংলা'},
    }
    
    for lang_code, metadata in lang_metadata.items():
        if (locales_dir / f'{lang_code}.json').exists():
            languages[lang_code] = metadata
    
    return languages

# Make function available to templates
def init_app(app):
    """Register helper functions with Flask app"""
    app.jinja_env.globals['t'] = get_translation  # Short alias
    app.jinja_env.globals['get_translation'] = get_translation
    app.jinja_env.globals['get_current_language'] = get_current_language
    app.jinja_env.globals['get_available_languages'] = get_available_languages

