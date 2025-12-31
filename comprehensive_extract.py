"""
Comprehensive extraction of ALL hardcoded strings including common UI words
"""
import re
import json
from pathlib import Path

def extract_comprehensive():
    """Extract all hardcoded strings comprehensively"""
    templates_dir = Path('templates')
    all_strings = {}
    
    # Common UI words that should be translated
    common_ui_words = [
        'My Profile', 'Eco Points', 'Day Streak', 'My Stats', 'Items Analyzed',
        'Recyclable Items', 'Marketplace Listings', 'Preferred Language', 'Voice Input',
        'Badge Level', 'Achievements', 'Available Achievements', 'Recent Rewards',
        'Date', 'Activity', 'Points', 'Ways to Earn Points', 'Member since',
        'Recycle Rookie', 'Plastic Hero', 'Recycle your first item',
        'Login', 'Create an Account', 'Enter your email', 'Enter your password',
        'Choose a username', 'Username must be', 'Recycling Marketplace',
        'Add New Item', 'How the Marketplace Works', 'Item Details',
        'Description', 'Location', 'Contact Information', 'Municipality Status',
        'Computer Vision Analysis', 'Project Details', 'Progress', 'Project Type',
        'Your Contribution', 'Top Contributor!', 'Project Timeline', 'Top Contributors',
        'Infrastructure Projects', 'Your Contribution', 'View Details',
        'Back to Projects', 'Verified by', 'Best Disposal Method',
        'Change Language', 'Enable voice input', 'Select Your Language',
        'Choose your preferred language', 'Try speaking in your selected language'
    ]
    
    # Load existing translations
    existing_translations = {}
    try:
        with open('locales/en.json', 'r', encoding='utf-8') as f:
            existing_translations = json.load(f)
    except:
        pass
    
    existing_values = set(existing_translations.values())
    
    # Add common UI words that aren't in translations yet
    new_strings = {}
    for word in common_ui_words:
        if word not in existing_values:
            # Create a key for it
            key_base = word.lower().replace(' ', '_').replace("'", '').replace(':', '')[:40]
            key = f"common.{key_base}"
            new_strings[key] = word
    
    # Now extract from templates
    for template_file in templates_dir.glob('*.html'):
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove script and style
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        found = []
        
        # Check for common UI words
        for word in common_ui_words:
            if word in content and word not in existing_values:
                # Check if it's not already translated
                if f"get_localized_string" not in content[:content.find(word)+100]:
                    found.append(word)
        
        # Find text in tags
        text_pattern = r'>([^<{]+)<'
        matches = re.findall(text_pattern, content)
        for match in matches:
            text = match.strip()
            if (text and len(text) > 2 and 
                not '{{' in text and not '{%' in text and 
                not 'get_localized_string' in text and
                text not in existing_values and
                (text[0].isupper() or text.lower() in ['yes', 'no', 'close', 'cancel', 'submit', 'save'])):
                if text not in found:
                    found.append(text)
        
        # Find placeholders
        placeholder_pattern = r'placeholder=["\']([^"\']+)["\']'
        placeholders = re.findall(placeholder_pattern, content, re.IGNORECASE)
        for p in placeholders:
            if (p and len(p) > 2 and 
                not '{{' in p and 
                p not in existing_values):
                if p not in found:
                    found.append(p)
        
        if found:
            all_strings[template_file.stem] = list(set(found))
    
    # Merge with common UI words
    for key, value in new_strings.items():
        if 'common' not in all_strings:
            all_strings['common'] = []
        if value not in all_strings['common']:
            all_strings['common'].append(value)
    
    return all_strings

def create_translation_map(all_strings):
    """Create translation key map"""
    translation_map = {}
    key_counter = {}
    
    for template_name, strings in all_strings.items():
        for string in strings:
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

if __name__ == '__main__':
    print("Comprehensive extraction...")
    all_strings = extract_comprehensive()
    
    total = sum(len(s) for s in all_strings.values())
    print(f"\nFound {total} strings across {len(all_strings)} templates:")
    for template, strings in all_strings.items():
        print(f"  {template}: {len(strings)} strings")
        for s in strings[:8]:
            print(f"    - {s[:60]}")
    
    translation_map = create_translation_map(all_strings)
    
    print(f"\nCreated {len(translation_map)} translation keys")
    
    # Save
    with open('all_remaining_strings.json', 'w', encoding='utf-8') as f:
        json.dump(translation_map, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved to all_remaining_strings.json")

