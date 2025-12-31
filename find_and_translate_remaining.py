"""
Find all remaining hardcoded English strings and translate them
"""
import re
import json
import os
from pathlib import Path
import google.generativeai as genai
import time

# Configure Gemini
api_key = os.environ.get("GEMINI_API_KEY", "AIzaSyACMoAYK8z_VrIR0U8LmOyjz-0C0BhDj2I")
genai.configure(api_key=api_key)

LANGUAGES = {
    'en': 'English',
    'hi': 'Hindi',
    'kn': 'Kannada',
    'ta': 'Tamil',
    'mr': 'Marathi',
    'bn': 'Bengali'
}

def find_hardcoded_strings():
    """Find all hardcoded English strings in templates"""
    templates_dir = Path('templates')
    all_strings = {}
    
    # Common patterns to find hardcoded text
    patterns = [
        (r'>([A-Z][^<{]+)<', 'text'),  # Text in tags
        (r'placeholder=["\']([^"\']+)["\']', 'placeholder'),
        (r'title=["\']([^"\']+)["\']', 'title'),
        (r'aria-label=["\']([^"\']+)["\']', 'aria-label'),
        (r'alt=["\']([^"\']+)["\']', 'alt'),
    ]
    
    for template_file in templates_dir.glob('*.html'):
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Skip if already using translation
        if 'get_localized_string' not in content:
            continue
        
        # Remove script and style blocks
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        found_strings = []
        for pattern, string_type in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                text = match.strip()
                # Skip if contains template syntax
                if '{{' in text or '{%' in text:
                    continue
                # Skip if too short
                if len(text) < 2:
                    continue
                # Skip if just numbers/punctuation
                if re.match(r'^[\d\s\W]+$', text):
                    continue
                # Skip if already translated
                if text.startswith('get_localized_string'):
                    continue
                # Must start with capital letter (likely English text)
                if text and text[0].isupper():
                    found_strings.append((string_type, text))
        
        if found_strings:
            all_strings[template_file.stem] = list(set(found_strings))
    
    return all_strings

def create_translation_keys(found_strings):
    """Create translation keys for found strings"""
    translation_map = {}
    key_counter = {}
    
    for template_name, strings in found_strings.items():
        for string_type, string in strings:
            # Generate key
            key_base = string.lower()
            key_base = re.sub(r'[^\w\s]', '', key_base)
            key_base = re.sub(r'\s+', '_', key_base)
            key_base = key_base[:40]
            
            key = f"{template_name}.{key_base}"
            
            # Handle duplicates
            if key in key_counter:
                key_counter[key] += 1
                key = f"{key}_{key_counter[key]}"
            else:
                key_counter[key] = 0
            
            translation_map[key] = string
    
    return translation_map

def translate_new_strings(new_strings_dict):
    """Translate new strings using Gemini"""
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    
    # Load existing translations
    existing_en = {}
    locales_dir = Path('locales')
    if (locales_dir / 'en.json').exists():
        with open(locales_dir / 'en.json', 'r', encoding='utf-8') as f:
            existing_en = json.load(f)
    
    # Add new strings to English
    existing_en.update(new_strings_dict)
    
    # Save updated English
    with open(locales_dir / 'en.json', 'w', encoding='utf-8') as f:
        json.dump(existing_en, f, indent=2, ensure_ascii=False)
    
    print(f"Added {len(new_strings_dict)} new strings to en.json")
    
    # Translate to other languages
    for lang_code in ['hi', 'kn', 'ta', 'mr', 'bn']:
        if lang_code == 'en':
            continue
        
        print(f"\nTranslating to {LANGUAGES[lang_code]}...")
        
        # Load existing translations
        existing_translations = {}
        lang_file = locales_dir / f'{lang_code}.json'
        if lang_file.exists():
            with open(lang_file, 'r', encoding='utf-8') as f:
                existing_translations = json.load(f)
        
        # Translate new strings only
        batch_size = 30
        items = list(new_strings_dict.items())
        translated_new = {}
        
        for i in range(0, len(items), batch_size):
            batch = dict(items[i:i+batch_size])
            
            prompt = f"""Translate these English UI strings to {LANGUAGES[lang_code]}. 
Return ONLY valid JSON with same keys and translated values.

{json.dumps(batch, indent=2, ensure_ascii=False)}"""
            
            try:
                response = model.generate_content(prompt, generation_config={"temperature": 0.2})
                response_text = response.text.strip()
                
                # Clean response
                if '```' in response_text:
                    lines = response_text.split('\n')
                    if lines[0].strip().startswith('```'):
                        lines = lines[1:]
                    if lines[-1].strip() == '```':
                        lines = lines[:-1]
                    response_text = '\n'.join(lines)
                
                batch_translated = json.loads(response_text)
                translated_new.update(batch_translated)
                print(f"  Batch {i//batch_size + 1} done")
                time.sleep(0.5)
            except Exception as e:
                print(f"  Error: {e}")
                translated_new.update(batch)  # Use English as fallback
        
        # Merge with existing
        existing_translations.update(translated_new)
        
        # Save
        with open(lang_file, 'w', encoding='utf-8') as f:
            json.dump(existing_translations, f, indent=2, ensure_ascii=False)
        
        print(f"  Saved {lang_code}.json")

if __name__ == '__main__':
    print("Finding hardcoded strings...")
    found_strings = find_hardcoded_strings()
    
    print(f"\nFound strings in {len(found_strings)} templates:")
    for template, strings in found_strings.items():
        print(f"  {template}: {len(strings)} strings")
    
    print("\nCreating translation keys...")
    new_strings = create_translation_keys(found_strings)
    
    print(f"\nCreated {len(new_strings)} new translation keys")
    print("\nSample keys:")
    for i, (key, value) in enumerate(list(new_strings.items())[:10]):
        print(f"  {key}: {value[:50]}...")
    
    # Save to file
    with open('new_strings_to_translate.json', 'w', encoding='utf-8') as f:
        json.dump(new_strings, f, indent=2, ensure_ascii=False)
    
    print("\nTranslating new strings...")
    translate_new_strings(new_strings)
    
    print("\nDone! New strings added to all translation files.")

