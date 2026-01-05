"""
Translate newly added keys to all languages using Gemini
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

# New keys that need translation
NEW_KEYS = {
    'index.analyze_item': 'Analyze Item',
    'index.analysis_results': 'Analysis Results',
    'index.copy_analysis': 'Copy analysis',
    'index.summary': 'Summary',
    'index.recycling': 'Recycling',
    'index.environmental_impact': 'Environmental Impact',
    'index.full_analysis': 'Full Analysis',
    'index.yes': 'Yes',
    'index.no': 'No'
}

def translate_keys():
    """Translate new keys to all languages"""
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    
    for lang_code, lang_name in LANGUAGES.items():
        print(f"\nTranslating to {lang_name}...")
        
        # Load existing translations
        lang_file = f'locales/{lang_code}.json'
        with open(lang_file, 'r', encoding='utf-8') as f:
            translations = json.load(f)
        
        # Translate new keys
        prompt = f"""Translate these English UI strings to {lang_name}. 
Return ONLY valid JSON with same keys and translated values.

{json.dumps(NEW_KEYS, indent=2, ensure_ascii=False)}"""
        
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
            
            # Save
            with open(lang_file, 'w', encoding='utf-8') as f:
                json.dump(translations, f, indent=2, ensure_ascii=False)
            
            print(f"  [OK] Saved {lang_code}.json")
            time.sleep(0.5)
        except Exception as e:
            print(f"  [ERROR] Error: {e}")
            # Use English as fallback
            translations.update(NEW_KEYS)
            with open(lang_file, 'w', encoding='utf-8') as f:
                json.dump(translations, f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    print("Translating new keys to all languages...")
    translate_keys()
    print("\nDone!")

