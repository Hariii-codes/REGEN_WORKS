"""
Script to translate all extracted strings using Gemini API
"""
import json
import os
import google.generativeai as genai
import time
import logging

logging.basicConfig(level=logging.INFO)

# Configure Gemini
api_key = os.environ.get("GEMINI_API_KEY", "AIzaSyACMoAYK8z_VrIR0U8LmOyjz-0C0BhDj2I")
genai.configure(api_key=api_key)

# Language codes and names
LANGUAGES = {
    'en': 'English',
    'hi': 'Hindi',
    'kn': 'Kannada',
    'ta': 'Tamil',
    'mr': 'Marathi',
    'bn': 'Bengali'
}

def translate_strings(strings_dict, target_language):
    """Translate a dictionary of strings to target language using Gemini"""
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    
    # If English, return as-is
    if target_language == 'en':
        return strings_dict
    
    target_lang_name = LANGUAGES[target_language]
    
    # Batch translate in chunks to avoid token limits
    translated = {}
    batch_size = 20
    items = list(strings_dict.items())
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        batch_dict = dict(batch)
        
        # Create prompt for translation
        prompt = f"""Translate the following English UI text strings to {target_lang_name}. 
Return ONLY a valid JSON object with the same keys and translated values. 
Do not include any explanations or markdown formatting, just the JSON.

English strings to translate:
{json.dumps(batch_dict, indent=2, ensure_ascii=False)}

Return the JSON object with translations:"""
        
        try:
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 2000,
                }
            )
            
            # Extract JSON from response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            if response_text.endswith('```'):
                response_text = response_text[:-3].strip()
            
            # Parse JSON
            try:
                batch_translated = json.loads(response_text)
                translated.update(batch_translated)
                logging.info(f"Translated batch {i//batch_size + 1}/{(len(items)-1)//batch_size + 1}")
            except json.JSONDecodeError as e:
                logging.error(f"JSON parse error for batch {i//batch_size + 1}: {e}")
                logging.error(f"Response was: {response_text[:200]}")
                # Fallback: use original strings
                translated.update(batch_dict)
            
            # Rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            logging.error(f"Error translating batch {i//batch_size + 1}: {e}")
            # Fallback: use original strings
            translated.update(batch_dict)
    
    return translated

def create_translation_files():
    """Create JSON translation files for all languages"""
    # Load extracted strings
    with open('extracted_strings.json', 'r', encoding='utf-8') as f:
        strings_dict = json.load(f)
    
    print(f"Translating {len(strings_dict)} strings to {len(LANGUAGES)} languages...")
    
    translations = {}
    for lang_code in LANGUAGES.keys():
        print(f"\nTranslating to {LANGUAGES[lang_code]}...")
        translated = translate_strings(strings_dict, lang_code)
        translations[lang_code] = translated
        
        # Save individual language file
        output_file = f'locales/{lang_code}.json'
        os.makedirs('locales', exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(translated, f, indent=2, ensure_ascii=False)
        print(f"Saved {output_file}")
    
    # Save combined file
    with open('locales/all_translations.json', 'w', encoding='utf-8') as f:
        json.dump(translations, f, indent=2, ensure_ascii=False)
    
    print("\nTranslation complete!")

if __name__ == '__main__':
    create_translation_files()

