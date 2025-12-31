"""
Localization Manager for ReGenWorks
Handles all 22 official Indian languages + English
"""

# Supported languages - ONLY English, Hindi, and Kannada
SUPPORTED_LANGUAGES = {
    'en': {'name': 'English', 'native': 'English', 'code': 'en'},
    'hi': {'name': 'Hindi', 'native': 'हिंदी', 'code': 'hi'},
    'kn': {'name': 'Kannada', 'native': 'ಕನ್ನಡ', 'code': 'kn'},
}

def get_language_name(code):
    """Get language name in English"""
    return SUPPORTED_LANGUAGES.get(code, {}).get('name', 'English')

def get_language_native(code):
    """Get language name in native script"""
    return SUPPORTED_LANGUAGES.get(code, {}).get('native', 'English')

def get_all_languages():
    """Get all supported languages"""
    return SUPPORTED_LANGUAGES

def is_valid_language(code):
    """Check if language code is valid"""
    return code in SUPPORTED_LANGUAGES

def get_default_language():
    """Get default language (English)"""
    return 'en'

