"""
Script to help identify and replace hardcoded strings in templates
This is a helper script - manual review and replacement is recommended
"""
import re
import json
from pathlib import Path

def load_translations():
    """Load all translations"""
    translations = {}
    locales_dir = Path('locales')
    
    for lang_file in locales_dir.glob('*.json'):
        lang_code = lang_file.stem
        with open(lang_file, 'r', encoding='utf-8') as f:
            translations[lang_code] = json.load(f)
    
    return translations

def find_hardcoded_strings(template_path, translations):
    """Find hardcoded strings that should be replaced"""
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Get English translations as reference
    en_translations = translations.get('en', {})
    
    # Create reverse lookup: value -> key
    value_to_key = {v: k for k, v in en_translations.items()}
    
    # Find text content in HTML tags
    text_pattern = r'>([^<{]+)<'
    matches = re.findall(text_pattern, content)
    
    replacements = []
    for match in matches:
        text = match.strip()
        # Skip if already using translation function
        if 'get_localized_string' in content or '{{ t(' in content:
            continue
        
        # Skip if it's a template variable
        if '{{' in text or '{%' in text:
            continue
        
        # Skip if too short
        if len(text) < 3:
            continue
        
        # Check if this text exists in translations
        if text in value_to_key:
            key = value_to_key[text]
            replacements.append({
                'original': text,
                'key': key,
                'line': content[:content.find(f'>{text}<')].count('\n') + 1
            })
    
    return replacements

def generate_replacement_suggestions():
    """Generate suggestions for replacing hardcoded strings"""
    translations = load_translations()
    templates_dir = Path('templates')
    
    all_replacements = {}
    
    for template_file in templates_dir.glob('*.html'):
        replacements = find_hardcoded_strings(template_file, translations)
        if replacements:
            all_replacements[template_file.name] = replacements
    
    # Save suggestions
    with open('replacement_suggestions.json', 'w', encoding='utf-8') as f:
        json.dump(all_replacements, f, indent=2, ensure_ascii=False)
    
    print(f"Found {sum(len(r) for r in all_replacements.values())} potential replacements")
    print("Saved to replacement_suggestions.json")
    
    # Print sample
    for template, replacements in list(all_replacements.items())[:3]:
        print(f"\n{template}:")
        for r in replacements[:5]:
            print(f"  '{r['original']}' -> {r['key']}")

if __name__ == '__main__':
    generate_replacement_suggestions()

