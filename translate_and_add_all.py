"""
Translate all remaining strings and add to translation files
Then add live language switching
"""
import json
import os
import google.generativeai as genai
import time

api_key = os.environ.get("GEMINI_API_KEY", "AIzaSyAixA3oohovvFAdewRF3xP4UHjympdlT18")
genai.configure(api_key=api_key)

LANGUAGES = {
    'hi': 'Hindi',
    'kn': 'Kannada',
    'ta': 'Tamil',
    'mr': 'Marathi',
    'bn': 'Bengali'
}

def translate_all_new_strings():
    """Translate all new strings to all languages"""
    # Load new strings
    with open('all_remaining_strings.json', 'r', encoding='utf-8') as f:
        new_strings = json.load(f)
    
    print(f"Translating {len(new_strings)} new strings...")
    
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    
    # Update English first
    with open('locales/en.json', 'r', encoding='utf-8') as f:
        en_translations = json.load(f)
    
    en_translations.update(new_strings)
    
    with open('locales/en.json', 'w', encoding='utf-8') as f:
        json.dump(en_translations, f, indent=2, ensure_ascii=False)
    
    print("Updated en.json")
    
    # Translate to other languages
    for lang_code, lang_name in LANGUAGES.items():
        print(f"\nTranslating to {lang_name}...")
        
        # Load existing
        lang_file = f'locales/{lang_code}.json'
        with open(lang_file, 'r', encoding='utf-8') as f:
            translations = json.load(f)
        
        # Translate in batches
        batch_size = 30
        items = list(new_strings.items())
        
        for i in range(0, len(items), batch_size):
            batch = dict(items[i:i+batch_size])
            
            prompt = f"""Translate these English UI strings to {lang_name}. 
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
                
                translated = json.loads(response_text)
                translations.update(translated)
                
                print(f"  Batch {i//batch_size + 1} done")
                time.sleep(0.5)
            except Exception as e:
                print(f"  Error: {e}")
                # Use English as fallback
                translations.update(batch)
        
        # Save
        with open(lang_file, 'w', encoding='utf-8') as f:
            json.dump(translations, f, indent=2, ensure_ascii=False)
        
        print(f"  Saved {lang_code}.json")
    
    print("\nAll translations complete!")

if __name__ == '__main__':
    translate_all_new_strings()

