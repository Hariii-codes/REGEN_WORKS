"""
Extract ALL remaining hardcoded strings from ALL templates
"""
import re
import json
from pathlib import Path

def extract_all_strings():
    """Extract all hardcoded strings from all templates"""
    templates_dir = Path('templates')
    all_strings = {}
    
    # Load existing translations to avoid duplicates
    existing_translations = {}
    try:
        with open('locales/en.json', 'r', encoding='utf-8') as f:
            existing_translations = json.load(f)
    except:
        pass
    
    existing_values = set(existing_translations.values())
    
    for template_file in templates_dir.glob('*.html'):
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove script and style blocks
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        found_strings = []
        
        # Find text in tags
        text_pattern = r'>([^<{]+)<'
        matches = re.findall(text_pattern, content)
        for match in matches:
            text = match.strip()
            if (text and len(text) > 2 and 
                not '{{' in text and not '{%' in text and 
                not 'get_localized_string' in text and
                text[0].isupper() and
                text not in existing_values):
                found_strings.append(text)
        
        # Find placeholders
        placeholder_pattern = r'placeholder=["\']([^"\']+)["\']'
        placeholders = re.findall(placeholder_pattern, content, re.IGNORECASE)
        for p in placeholders:
            if (p and len(p) > 2 and 
                not '{{' in p and 
                p not in existing_values):
                found_strings.append(p)
        
        # Find titles
        title_pattern = r'title=["\']([^"\']+)["\']'
        titles = re.findall(title_pattern, content, re.IGNORECASE)
        for t in titles:
            if (t and len(t) > 2 and 
                not '{{' in t and 
                t not in existing_values):
                found_strings.append(t)
        
        if found_strings:
            all_strings[template_file.stem] = list(set(found_strings))
    
    return all_strings

def create_keys(all_strings):
    """Create translation keys"""
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
    print("Extracting ALL remaining strings...")
    all_strings = extract_all_strings()
    
    total = sum(len(s) for s in all_strings.values())
    print(f"\nFound {total} strings across {len(all_strings)} templates:")
    for template, strings in all_strings.items():
        print(f"  {template}: {len(strings)} strings")
        for s in strings[:5]:
            print(f"    - {s[:50]}")
    
    print("\nCreating translation keys...")
    translation_map = create_keys(all_strings)
    
    print(f"\nCreated {len(translation_map)} new keys")
    
    # Save
    with open('all_remaining_strings.json', 'w', encoding='utf-8') as f:
        json.dump(translation_map, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved to all_remaining_strings.json")

