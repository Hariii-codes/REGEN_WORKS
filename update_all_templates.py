#!/usr/bin/env python3
"""
Script to update all templates to use eco-themed design
"""

import os
import glob

# List of templates to update to use eco theme
templates_to_update = [
    ('index.html', 'index-eco.html'),
    ('drop_points.html', 'drop_points-eco.html'),
    ('profile.html', 'profile-eco.html'),
    ('footprint_dashboard.html', 'footprint_dashboard-eco.html'),
]

def update_template_content(template_path):
    """Update a single template to use eco design system"""
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Replace base template reference if needed
        if 'extends "base.html"' in content:
            content = content.replace('extends "base.html"', 'extends "base-eco.html"')
            print(f"✓ Updated {os.path.basename(template_path)} to use base-eco.html")

        # Write back the updated content
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True
    except Exception as e:
        print(f"✗ Error updating {template_path}: {e}")
        return False

def main():
    templates_dir = 'templates'

    print("Updating templates to use eco design system...")

    # First update all regular templates to use base-eco.html
    for template_file in os.listdir(templates_dir):
        if template_file.endswith('.html') and not template_file.startswith('base-'):
            template_path = os.path.join(templates_dir, template_file)
            update_template_content(template_path)

    print("\n✅ All templates updated to use eco design system!")
    print("\nTo ensure all pages use the new design:")
    print("1. Restart your Flask server")
    print("2. Clear browser cache (Ctrl+R or Cmd+Shift+R)")
    print("3. All pages should now have improved text visibility")

if __name__ == "__main__":
    main()