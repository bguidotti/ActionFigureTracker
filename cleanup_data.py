#!/usr/bin/env python3
"""
Clean up figure data:
1. Remove entries that are just accessories (not actual figures)
2. Clean names that have accessories appended after a dash
"""

import json
import re
import sys

sys.stdout.reconfigure(line_buffering=True)

JSON_FILE = r'c:\Code\ActionFigureTracker\Models\all_figures.json'

# Entries that are clearly just accessories, not figures
ACCESSORY_ONLY_PATTERNS = [
    r'^Sword$',
    r'^Sword, shield',
    r'^Batarang',
    r'^Kryptonite spear',
    r'^Display',
    r'^Stand$',
    r'^Dagger$',
    r'^2 alternate hands',
    r'^Alternate hands',
    r'^Flight stand',
    r'^Art card',
    r'and card$',  # Entries ending with "and card"
]

# Patterns that indicate accessories in name (after dash)
ACCESSORIES_IN_NAME_PATTERNS = [
    r' - (Flight stand|Lights|Card|Display|Massive display|Chained hook|Throne|Camera|Smoke effect|Grapple launcher)',
]


def is_accessory_only(name: str) -> bool:
    """Check if this entry is just an accessory, not a figure"""
    for pattern in ACCESSORY_ONLY_PATTERNS:
        if re.match(pattern, name, re.IGNORECASE):
            return True
    return False


def clean_name(name: str) -> str:
    """Remove accessories appended after dash"""
    # Pattern: "Figure Name - accessory list"
    # Keep the figure name, remove the accessories
    # But only if the part after dash looks like accessories
    
    parts = name.split(' - ', 1)
    if len(parts) == 2:
        after_dash = parts[1].lower()
        accessory_keywords = [
            'flight stand', 'display', 'card', 'base', 'backdrop',
            'lights', 'sounds', 'miniature', 'throne', 'spear',
            'camera', 'smoke effect', 'grapple', 'chained', 'hook',
            'guitar', 'alternate head'
        ]
        if any(kw in after_dash for kw in accessory_keywords):
            return parts[0].strip()
    
    return name


def main():
    print(f"Loading {JSON_FILE}...")
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        figures = json.load(f)
    
    original_count = len(figures)
    print(f"Loaded {original_count} figures")
    
    # Track changes
    removed = []
    cleaned = []
    
    cleaned_figures = []
    for fig in figures:
        name = fig.get('name', '')
        
        # Skip accessory-only entries
        if is_accessory_only(name):
            removed.append(name)
            continue
        
        # Clean name if it has accessories appended
        new_name = clean_name(name)
        if new_name != name:
            cleaned.append((name, new_name))
            fig['name'] = new_name
        
        cleaned_figures.append(fig)
    
    # Re-index IDs
    for i, fig in enumerate(cleaned_figures):
        fig['id'] = i + 1
    
    print(f"\n=== Removed {len(removed)} accessory-only entries ===")
    for name in removed:
        print(f"  - {name}")
    
    print(f"\n=== Cleaned {len(cleaned)} names ===")
    for old, new in cleaned:
        print(f"  - '{old}' -> '{new}'")
    
    print(f"\nFinal count: {len(cleaned_figures)} (was {original_count})")
    
    # Save
    print(f"\nSaving to {JSON_FILE}...")
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(cleaned_figures, f, indent=2)
    
    print("Done!")


if __name__ == '__main__':
    main()
