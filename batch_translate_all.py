"""
Batch translation script - Translates ALL strings in ONE API call.
Extracts all strings from en.json and translates them to all target languages in a single batch request.
"""

import json
import google.generativeai as genai
import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)

# Configure Google Gemini AI with API key
api_key = os.environ.get("GEMINI_API_KEY", "AIzaSyAixA3oohovvFAdewRF3xP4UHjympdlT18")
genai.configure(api_key=api_key)

# Target languages - ONLY Hindi and Kannada
TARGET_LANGUAGES = {
    'hi': 'Hindi',
    'kn': 'Kannada'
}

def load_english_strings():
    """Load all English strings from en.json"""
    locales_dir = Path('locales')
    # Try src/locales first, then locales
    src_locales_dir = Path('src/locales')
    if src_locales_dir.exists():
        en_file = src_locales_dir / 'en.json'
    else:
        en_file = locales_dir / 'en.json'
    
    if not en_file.exists():
        raise FileNotFoundError(f"English localization file not found: {en_file}")
    
    with open(en_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def translate_all_strings_batch(strings_dict, target_language):
    """
    Translate ALL strings in ONE batch API call.
    
    Args:
        strings_dict: Dictionary of all English strings
        target_language: Target language code (e.g., 'hi')
        
    Returns:
        Dictionary with translated strings
    """
    target_lang_name = TARGET_LANGUAGES.get(target_language)
    if not target_lang_name:
        logging.error(f"Unsupported language: {target_language}")
        return {}
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        
        # Convert dictionary to JSON string for batch translation
        json_string = json.dumps(strings_dict, ensure_ascii=False, indent=2)
        
        # Create prompt for batch translation
        prompt = f"""Translate the following JSON file containing all user-facing strings to {target_lang_name}.

CRITICAL RULES:
1. Translate ONLY the VALUES (right side of colons), NOT the keys (left side)
2. Preserve ALL JSON structure, keys, and formatting exactly
3. Keep placeholders like {{variable}} exactly as they are
4. Preserve HTML tags and structure
5. Do NOT rewrite or improve the text - only translate
6. Return ONLY the translated JSON, no explanations

JSON to translate:
{json_string}"""
        
        logging.info(f"Translating {len(strings_dict)} strings to {target_lang_name} in ONE batch request...")
        
        response = model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": 8000,  # Large token limit for batch
                "temperature": 0.1,  # Low temperature for literal translation
            }
        )
        
        # Extract JSON from response
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            # Find the first newline after ```
            start_idx = response_text.find('\n') + 1
            # Find the last ``` before the end
            end_idx = response_text.rfind('```')
            if end_idx > start_idx:
                response_text = response_text[start_idx:end_idx].strip()
            else:
                response_text = response_text[start_idx:].strip()
        
        # Parse the translated JSON
        translated_dict = json.loads(response_text)
        
        logging.info(f"Successfully translated {len(translated_dict)} strings to {target_lang_name}")
        return translated_dict
        
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing translated JSON: {e}")
        logging.error(f"Response text: {response_text[:500]}")
        return {}
    except Exception as e:
        logging.error(f"Error translating to {target_lang_name}: {e}")
        return {}

def save_translated_file(translated_dict, language_code):
    """Save translated strings to language JSON file"""
    # Try src/locales first, then locales
    src_locales_dir = Path('src/locales')
    locales_dir = Path('locales')
    
    if src_locales_dir.exists():
        output_dir = src_locales_dir
    else:
        output_dir = locales_dir
        output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / f'{language_code}.json'
    
    # Sort keys for readability
    sorted_dict = dict(sorted(translated_dict.items()))
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sorted_dict, f, ensure_ascii=False, indent=2)
    
    logging.info(f"Saved {len(sorted_dict)} translated strings to {output_file}")

def main():
    """Main function to translate all strings"""
    # Load English strings
    logging.info("Loading English strings from en.json...")
    english_strings = load_english_strings()
    logging.info(f"Loaded {len(english_strings)} English strings")
    
    # Translate to each target language in ONE batch request per language
    for lang_code, lang_name in TARGET_LANGUAGES.items():
        logging.info(f"\n{'='*60}")
        logging.info(f"Translating to {lang_name} ({lang_code})...")
        logging.info(f"{'='*60}")
        
        # Translate ALL strings in ONE batch request
        translated = translate_all_strings_batch(english_strings, lang_code)
        
        if translated:
            # Save translated file
            save_translated_file(translated, lang_code)
            logging.info(f"✓ Completed translation to {lang_name}")
        else:
            logging.error(f"✗ Failed to translate to {lang_name}")
    
    logging.info("\n" + "="*60)
    logging.info("Batch translation complete!")
    logging.info("="*60)

if __name__ == "__main__":
    main()

