"""
Translate ALL newly added keys to all languages using Gemini
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

def get_new_keys():
    """Get all new keys that need translation"""
    # Load all remaining strings
    with open('all_remaining_strings.json', 'r', encoding='utf-8') as f:
        remaining = json.load(f)
    
    # Load current English translations
    with open('locales/en.json', 'r', encoding='utf-8') as f:
        en_translations = json.load(f)
    
    # Find keys that are in en.json but might not be in other languages
    # For now, just translate the remaining strings
    return remaining

def translate_all():
    """Translate all new keys to all languages"""
    new_keys = get_new_keys()
    
    # Also add common profile keys
    profile_keys = {
        'profile.my_profile': 'My Profile',
        'profile.eco_points': 'Eco Points',
        'profile.day_streak': 'Day Streak',
        'profile.my_stats': 'My Stats',
        'profile.items_analyzed': 'Items Analyzed',
        'profile.recyclable_items': 'Recyclable Items',
        'profile.ewaste_items': 'E-Waste Items',
        'profile.marketplace_listings': 'Marketplace Listings',
        'profile.achievements': 'Achievements',
        'profile.preferred_language': 'Preferred Language',
        'profile.voice_input': 'Voice Input',
        'profile.badge_level': 'Badge Level',
        'profile.available_achievements': 'Available Achievements',
        'profile.recent_rewards': 'Recent Rewards',
        'profile.date': 'Date',
        'profile.activity': 'Activity',
        'profile.points': 'Points',
        'profile.ways_to_earn_points': 'Ways to Earn Points',
        'profile.member_since': 'Member since',
        'profile.change_language': 'Change Language',
        'profile.enable_voice_input': 'Enable voice input',
        'profile.settings': 'Settings',
        'profile.recycle_rookie': 'Recycle Rookie',
        'profile.plastic_hero': 'Plastic Hero',
        'profile.recycle_your_first_item': 'Recycle your first item',
        'marketplace.recycling_marketplace': 'Recycling Marketplace',
        'marketplace.add_new_item': 'Add New Item',
        'marketplace.how_marketplace_works': 'How the Marketplace Works',
        'auth.create_account': 'Create an Account'
    }
    
    # Merge
    all_new_keys = {**new_keys, **profile_keys}
    
    print(f"Translating {len(all_new_keys)} new keys...")
    
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    
    # Update English first
    with open('locales/en.json', 'r', encoding='utf-8') as f:
        en_translations = json.load(f)
    
    en_translations.update(all_new_keys)
    
    with open('locales/en.json', 'w', encoding='utf-8') as f:
        json.dump(en_translations, f, indent=2, ensure_ascii=False)
    
    print("Updated en.json")
    
    # Translate to other languages
    for lang_code, lang_name in LANGUAGES.items():
        print(f"\nTranslating to {lang_name}...")
        
        lang_file = f'locales/{lang_code}.json'
        with open(lang_file, 'r', encoding='utf-8') as f:
            translations = json.load(f)
        
        # Translate in batches
        batch_size = 30
        items = list(all_new_keys.items())
        
        for i in range(0, len(items), batch_size):
            batch = dict(items[i:i+batch_size])
            
            prompt = f"""Translate these English UI strings to {lang_name}. 
Return ONLY valid JSON with same keys and translated values.

{json.dumps(batch, indent=2, ensure_ascii=False)}"""
            
            try:
                response = model.generate_content(prompt, generation_config={"temperature": 0.2})
                response_text = response.text.strip()
                
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
                translations.update(batch)  # Use English as fallback
        
        # Save
        with open(lang_file, 'w', encoding='utf-8') as f:
            json.dump(translations, f, indent=2, ensure_ascii=False)
        
        print(f"  Saved {lang_code}.json")
    
    print("\nAll translations complete!")

if __name__ == '__main__':
    translate_all()

