"""
Clean extracted strings and translate using Gemini
"""
import json
import os
import google.generativeai as genai
import time
import logging
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

def clean_strings(strings_dict):
    """Clean extracted strings - remove template variables, duplicates, etc."""
    cleaned = {}
    
    for key, value in strings_dict.items():
        # Skip if contains template syntax
        if '{{' in value or '{%' in value:
            continue
        
        # Skip if too short or just punctuation
        value_clean = value.strip()
        if len(value_clean) < 2:
            continue
        
        # Skip if just numbers or special chars
        if re.match(r'^[\d\s\W]+$', value_clean):
            continue
        
        # Skip common HTML entities and fragments
        if value_clean in ['&copy;', '|', '-', '/', '...']:
            continue
        
        # Clean up the value
        value_clean = ' '.join(value_clean.split())
        cleaned[key] = value_clean
    
    return cleaned

def translate_batch(model, batch_dict, target_lang_name):
    """Translate a batch of strings"""
    prompt = f"""You are a professional translator. Translate the following English UI text strings to {target_lang_name}.

IMPORTANT RULES:
1. Return ONLY valid JSON, no explanations
2. Keep the same keys
3. Translate values to {target_lang_name}
4. Maintain UI context (buttons, labels, messages)
5. Keep technical terms in English if commonly used (e.g., "API", "JSON")
6. Preserve HTML entities like &copy; as-is

English strings:
{json.dumps(batch_dict, indent=2, ensure_ascii=False)}

Return the JSON translation:"""
    
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": 4000,
            }
        )
        
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if '```' in response_text:
            lines = response_text.split('\n')
            # Remove first line if it's ```json or ```
            if lines[0].strip().startswith('```'):
                lines = lines[1:]
            # Remove last line if it's ```
            if lines[-1].strip() == '```':
                lines = lines[:-1]
            response_text = '\n'.join(lines)
        
        # Parse JSON
        try:
            translated = json.loads(response_text)
            return translated
        except json.JSONDecodeError as e:
            logging.error(f"JSON parse error: {e}")
            logging.error(f"Response preview: {response_text[:500]}")
            return None
            
    except Exception as e:
        logging.error(f"Translation error: {e}")
        return None

def translate_strings(strings_dict, target_language):
    """Translate a dictionary of strings to target language using Gemini"""
    # If English, return as-is
    if target_language == 'en':
        return strings_dict
    
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    target_lang_name = LANGUAGES[target_language]
    
    # Batch translate in chunks
    translated = {}
    batch_size = 30  # Increased batch size
    items = list(strings_dict.items())
    total_batches = (len(items) - 1) // batch_size + 1
    
    logging.info(f"Translating {len(items)} strings to {target_lang_name} in {total_batches} batches...")
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        batch_dict = dict(batch)
        batch_num = i // batch_size + 1
        
        logging.info(f"Translating batch {batch_num}/{total_batches} ({len(batch_dict)} strings)...")
        
        result = translate_batch(model, batch_dict, target_lang_name)
        
        if result:
            translated.update(result)
            logging.info(f"[OK] Batch {batch_num} completed")
        else:
            logging.warning(f"[FAIL] Batch {batch_num} failed, using original strings")
            translated.update(batch_dict)
        
        # Rate limiting
        if i + batch_size < len(items):
            time.sleep(1)  # Be respectful to API
    
    # Fill in any missing keys with original
    for key in strings_dict:
        if key not in translated:
            translated[key] = strings_dict[key]
    
    return translated

def create_translation_files():
    """Create JSON translation files for all languages"""
    # Load extracted strings
    print("Loading extracted strings...")
    with open('extracted_strings.json', 'r', encoding='utf-8') as f:
        strings_dict = json.load(f)
    
    print(f"Found {len(strings_dict)} strings")
    
    # Clean strings
    print("Cleaning strings...")
    cleaned_strings = clean_strings(strings_dict)
    print(f"After cleaning: {len(cleaned_strings)} strings")
    
    # Save cleaned English version
    os.makedirs('locales', exist_ok=True)
    with open('locales/en.json', 'w', encoding='utf-8') as f:
        json.dump(cleaned_strings, f, indent=2, ensure_ascii=False)
    print("Saved locales/en.json")
    
    # Translate to other languages
    for lang_code in ['hi', 'kn', 'ta', 'mr', 'bn']:
        output_file = f'locales/{lang_code}.json'
        
        # Skip if already exists
        if os.path.exists(output_file):
            print(f"\nSkipping {LANGUAGES[lang_code]} - file already exists")
            continue
        
        print(f"\n{'='*60}")
        print(f"Translating to {LANGUAGES[lang_code]} ({lang_code})...")
        print(f"{'='*60}")
        
        translated = translate_strings(cleaned_strings, lang_code)
        
        # Save individual language file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(translated, f, indent=2, ensure_ascii=False)
        print(f"[OK] Saved {output_file}")
    
    print(f"\n{'='*60}")
    print("Translation complete!")
    print(f"{'='*60}")

if __name__ == '__main__':
    create_translation_files()

