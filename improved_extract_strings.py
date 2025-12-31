"""
Improved script to extract all user-visible strings from templates
with better key generation matching existing localization structure
"""
import re
import os
import json
from pathlib import Path
from collections import defaultdict

def extract_strings_from_template(file_path):
    """Extract all user-visible strings from an HTML template"""
    strings = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove script and style blocks
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
    content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
    
    # Extract text from HTML tags (excluding template variables)
    # Match text that's not inside template tags or HTML attributes
    text_pattern = r'>([^<{]+)<'
    matches = re.findall(text_pattern, content)
    
    for match in matches:
        text = match.strip()
        # Filter out empty strings, whitespace-only, and template variables
        if text and len(text) > 1 and not text.startswith('{%') and not text.startswith('{{'):
            # Remove extra whitespace
            text = ' '.join(text.split())
            # Skip if it's just punctuation or numbers
            if text and not re.match(r'^[\d\s\W]+$', text):
                strings.append(('text', text))
    
    # Extract placeholder text
    placeholder_pattern = r'placeholder=["\']([^"\']+)["\']'
    placeholders = re.findall(placeholder_pattern, content, re.IGNORECASE)
    for p in placeholders:
        if p and not p.startswith('{{'):
            strings.append(('placeholder', p))
    
    # Extract title attributes
    title_pattern = r'title=["\']([^"\']+)["\']'
    titles = re.findall(title_pattern, content, re.IGNORECASE)
    for t in titles:
        if t and not t.startswith('{{'):
            strings.append(('title', t))
    
    # Extract aria-label attributes
    aria_pattern = r'aria-label=["\']([^"\']+)["\']'
    aria_labels = re.findall(aria_pattern, content, re.IGNORECASE)
    for a in aria_labels:
        if a and not a.startswith('{{'):
            strings.append(('aria-label', a))
    
    # Extract alt text
    alt_pattern = r'alt=["\']([^"\']+)["\']'
    alt_texts = re.findall(alt_pattern, content, re.IGNORECASE)
    for alt in alt_texts:
        if alt and not alt.startswith('{{'):
            strings.append(('alt', alt))
    
    return strings

def create_smart_key(template_name, string_type, string, existing_keys):
    """Create a smart translation key based on context"""
    # Common patterns to map to existing keys
    key_mappings = {
        'analyze waste': 'nav.analyze',
        'marketplace': 'nav.marketplace',
        'municipality': 'nav.municipality',
        'drop points': 'nav.drop_points',
        'my profile': 'nav.profile',
        'login': 'auth.login',
        'logout': 'auth.logout',
        'register': 'auth.register',
        'cancel': 'common.cancel',
        'submit': 'common.submit',
        'save': 'common.save',
        'delete': 'common.delete',
        'edit': 'common.edit',
        'search': 'common.search',
        'filter': 'common.filter',
        'loading': 'common.loading',
        'error': 'common.error',
        'success': 'common.success',
        'warning': 'common.warning',
        'info': 'common.info',
    }
    
    # Check if string matches a common pattern
    string_lower = string.lower().strip()
    for pattern, key in key_mappings.items():
        if pattern in string_lower:
            if key not in existing_keys:
                return key
    
    # Generate key from string
    key_base = string_lower
    # Remove special characters but keep spaces for now
    key_base = re.sub(r'[^\w\s]', '', key_base)
    # Replace spaces with underscores
    key_base = re.sub(r'\s+', '_', key_base)
    # Limit length
    key_base = key_base[:40]
    
    # Add prefix based on template
    template_prefix = template_name.replace('_', '.')
    key = f"{template_prefix}.{key_base}"
    
    # Handle duplicates
    if key in existing_keys:
        counter = 1
        while f"{key}_{counter}" in existing_keys:
            counter += 1
        key = f"{key}_{counter}"
    
    return key

def extract_all_strings():
    """Extract all strings from all templates with smart key generation"""
    templates_dir = Path('templates')
    all_strings = {}
    existing_keys = set()
    
    for template_file in templates_dir.glob('*.html'):
        strings = extract_strings_from_template(template_file)
        if strings:
            template_dict = {}
            for string_type, string in strings:
                # Skip if already processed
                if string in [v for values in all_strings.values() for v in values.values()]:
                    continue
                
                key = create_smart_key(template_file.stem, string_type, string, existing_keys)
                existing_keys.add(key)
                template_dict[key] = string
            
            if template_dict:
                all_strings[template_file.stem] = template_dict
    
    # Flatten to single dictionary
    flattened = {}
    for template_dict in all_strings.values():
        flattened.update(template_dict)
    
    return flattened

if __name__ == '__main__':
    print("Extracting strings from templates with smart key generation...")
    translation_map = extract_all_strings()
    
    print(f"Found {len(translation_map)} unique translation keys")
    
    # Save to JSON
    output_file = 'extracted_strings.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(translation_map, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved translation keys to {output_file}")
    
    # Print sample
    print("\nSample keys:")
    for i, (key, value) in enumerate(list(translation_map.items())[:20]):
        print(f"  {key}: {value[:60]}...")

