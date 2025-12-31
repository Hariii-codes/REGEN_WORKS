"""
Find ALL remaining hardcoded English strings in ALL templates
"""
import re
import json
from pathlib import Path
from collections import defaultdict

def find_all_hardcoded_strings():
    """Find all hardcoded English strings in all templates"""
    templates_dir = Path('templates')
    all_strings = defaultdict(list)
    
    # Patterns to find hardcoded text
    patterns = [
        (r'>([A-Z][^<{]+)<', 'text'),  # Text in tags starting with capital
        (r'placeholder=["\']([^"\']+)["\']', 'placeholder'),
        (r'title=["\']([^"\']+)["\']', 'title'),
        (r'aria-label=["\']([^"\']+)["\']', 'aria-label'),
        (r'alt=["\']([^"\']+)["\']', 'alt'),
        (r'value=["\']([^"\']+)["\']', 'value'),  # Button values
    ]
    
    # Load existing translations to avoid duplicates
    existing_translations = {}
    try:
        with open('locales/en.json', 'r', encoding='utf-8') as f:
            existing_translations = json.load(f)
    except:
        pass
    
    for template_file in templates_dir.glob('*.html'):
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove script and style blocks
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        found_strings = []
        for pattern, string_type in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                text = match.strip()
                
                # Skip if contains template syntax
                if '{{' in text or '{%' in text or 'get_localized_string' in text:
                    continue
                
                # Skip if too short
                if len(text) < 2:
                    continue
                
                # Skip if just numbers/punctuation
                if re.match(r'^[\d\s\W]+$', text):
                    continue
                
                # Skip common HTML entities
                if text in ['&copy;', '|', '-', '/', '...', ':', ';']:
                    continue
                
                # Skip if already in translations
                if text in existing_translations.values():
                    continue
                
                # Must start with capital letter or be a common UI word
                if text and (text[0].isupper() or text.lower() in ['yes', 'no', 'close', 'cancel', 'submit', 'save', 'delete', 'edit']):
                    # Clean the text
                    text_clean = ' '.join(text.split())
                    if text_clean and text_clean not in [s[1] for s in found_strings]:
                        found_strings.append((string_type, text_clean))
        
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

if __name__ == '__main__':
    print("Finding ALL remaining hardcoded strings...")
    found_strings = find_all_hardcoded_strings()
    
    total = sum(len(s) for s in found_strings.values())
    print(f"\nFound {total} strings across {len(found_strings)} templates:")
    for template, strings in found_strings.items():
        print(f"  {template}: {len(strings)} strings")
        for stype, text in strings[:5]:
            print(f"    - {text[:50]}")
    
    print("\nCreating translation keys...")
    translation_map = create_translation_keys(found_strings)
    
    print(f"\nCreated {len(translation_map)} new translation keys")
    
    # Save to file
    with open('all_remaining_strings.json', 'w', encoding='utf-8') as f:
        json.dump(translation_map, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved to all_remaining_strings.json")
    print("\nSample keys:")
    for i, (key, value) in enumerate(list(translation_map.items())[:15]):
        print(f"  {key}: {value[:60]}...")

