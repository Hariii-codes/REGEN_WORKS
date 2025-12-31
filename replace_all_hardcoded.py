"""
Replace all hardcoded English strings with translation function calls
"""
import re
import json
from pathlib import Path

def load_all_translations():
    """Load all translation keys"""
    with open('locales/en.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def create_replacement_map(translations):
    """Create map of English text to translation keys"""
    replacement_map = {}
    for key, value in translations.items():
        # Create variations
        replacement_map[value] = key
        replacement_map[value.strip()] = key
        # Also map common variations
        if value.endswith(':'):
            replacement_map[value[:-1]] = key
    
    return replacement_map

def replace_in_template(template_path, replacement_map):
    """Replace hardcoded strings in a template"""
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    replacements_made = []
    
    # Sort by length (longest first) to avoid partial matches
    sorted_replacements = sorted(replacement_map.items(), key=lambda x: len(x[0]), reverse=True)
    
    for english_text, key in sorted_replacements:
        # Skip if too short or common
        if len(english_text) < 3:
            continue
        
        # Skip if already translated
        if f"get_localized_string('{key}'" in content:
            continue
        
        # Create pattern to match the text in HTML
        # Match text in tags: >Text<
        pattern1 = rf'>\s*{re.escape(english_text)}\s*<'
        replacement1 = f">{{ get_localized_string('{key}', get_current_language(), '{english_text}') }}<"
        
        # Match in attributes: placeholder="Text"
        pattern2 = rf'placeholder=["\']{re.escape(english_text)}["\']'
        replacement2 = f'placeholder="{{ get_localized_string(\'{key}\', get_current_language(), \'{english_text}\') }}"'
        
        # Match in title: title="Text"
        pattern3 = rf'title=["\']{re.escape(english_text)}["\']'
        replacement3 = f'title="{{ get_localized_string(\'{key}\', get_current_language(), \'{english_text}\') }}"'
        
        # Match in aria-label
        pattern4 = rf'aria-label=["\']{re.escape(english_text)}["\']'
        replacement4 = f'aria-label="{{ get_localized_string(\'{key}\', get_current_language(), \'{english_text}\') }}"'
        
        # Apply replacements
        for pattern, replacement in [(pattern1, replacement1), (pattern2, replacement2), 
                                     (pattern3, replacement3), (pattern4, replacement4)]:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                replacements_made.append((english_text, key))
                break
    
    if content != original_content:
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return replacements_made
    return []

def main():
    """Main function"""
    print("Loading translations...")
    translations = load_all_translations()
    replacement_map = create_replacement_map(translations)
    
    print(f"Loaded {len(replacement_map)} replacement mappings")
    
    templates_dir = Path('templates')
    all_replacements = {}
    
    for template_file in templates_dir.glob('*.html'):
        print(f"\nProcessing {template_file.name}...")
        replacements = replace_in_template(template_file, replacement_map)
        if replacements:
            all_replacements[template_file.name] = replacements
            print(f"  Made {len(replacements)} replacements")
            for eng, key in replacements[:5]:
                print(f"    '{eng}' -> {key}")
    
    print(f"\n\nTotal replacements: {sum(len(r) for r in all_replacements.values())}")
    print("\nDone!")

if __name__ == '__main__':
    main()

