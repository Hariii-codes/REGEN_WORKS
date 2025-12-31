"""
Script to extract all user-visible strings from templates
"""
import re
import os
import json
from pathlib import Path

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
            if text and text not in strings:
                strings.append(text)
    
    # Extract placeholder text
    placeholder_pattern = r'placeholder=["\']([^"\']+)["\']'
    placeholders = re.findall(placeholder_pattern, content, re.IGNORECASE)
    strings.extend(placeholders)
    
    # Extract title attributes
    title_pattern = r'title=["\']([^"\']+)["\']'
    titles = re.findall(title_pattern, content, re.IGNORECASE)
    strings.extend(titles)
    
    # Extract aria-label attributes
    aria_pattern = r'aria-label=["\']([^"\']+)["\']'
    aria_labels = re.findall(aria_pattern, content, re.IGNORECASE)
    strings.extend(aria_labels)
    
    # Extract alt text
    alt_pattern = r'alt=["\']([^"\']+)["\']'
    alt_texts = re.findall(alt_pattern, content, re.IGNORECASE)
    strings.extend(alt_texts)
    
    return list(set(strings))  # Remove duplicates

def extract_all_strings():
    """Extract all strings from all templates"""
    templates_dir = Path('templates')
    all_strings = {}
    
    for template_file in templates_dir.glob('*.html'):
        strings = extract_strings_from_template(template_file)
        if strings:
            all_strings[template_file.stem] = strings
    
    return all_strings

def generate_translation_keys(all_strings):
    """Generate translation keys for all extracted strings"""
    translation_map = {}
    key_counter = {}
    
    for template_name, strings in all_strings.items():
        for string in strings:
            # Skip if already processed or if it's a template variable
            if '{{' in string or '{%' in string:
                continue
            
            # Generate a key based on the string
            # Create a readable key from the string
            key_base = string.lower()
            key_base = re.sub(r'[^a-z0-9\s]', '', key_base)
            key_base = re.sub(r'\s+', '_', key_base)
            key_base = key_base[:50]  # Limit length
            
            # Handle duplicates
            if key_base in key_counter:
                key_counter[key_base] += 1
                key = f"{template_name}.{key_base}_{key_counter[key_base]}"
            else:
                key_counter[key_base] = 0
                key = f"{template_name}.{key_base}"
            
            translation_map[key] = string
    
    return translation_map

if __name__ == '__main__':
    print("Extracting strings from templates...")
    all_strings = extract_all_strings()
    
    print(f"Found {sum(len(s) for s in all_strings.values())} strings across {len(all_strings)} templates")
    
    print("\nGenerating translation keys...")
    translation_map = generate_translation_keys(all_strings)
    
    # Save to JSON
    output_file = 'extracted_strings.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(translation_map, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved {len(translation_map)} translation keys to {output_file}")
    
    # Print sample
    print("\nSample keys:")
    for i, (key, value) in enumerate(list(translation_map.items())[:10]):
        print(f"  {key}: {value}")

