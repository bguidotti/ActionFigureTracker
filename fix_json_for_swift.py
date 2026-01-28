#!/usr/bin/env python3
"""
Fix JSON to match Swift model expectations
"""

import json
import sys

sys.stdout.reconfigure(line_buffering=True)

JSON_FILE = r'c:\Code\ActionFigureTracker\Models\all_figures.json'

# Map our series values to Swift FigureLine raw values
SERIES_TO_LINE = {
    'dc-multiverse': 'DC Multiverse',
    'dc-page-punchers': 'DC Multiverse',  # Integrate into Multiverse
    'dc-super-powers': 'DC Super Powers',
    'dc-retro': 'DC Retro',
    'dc-direct': 'DC Direct',
    'marvel-legends': 'Marvel Legends',
    'masters-of-the-universe-origins': 'MOTU Origins',
    'masters-of-the-universe-masterverse': 'MOTU Masterverse',
    'star-wars-black-series': 'Star Wars Black Series',
}

# Map status values
STATUS_MAP = {
    'want': 'I Want It!',
    'have': 'I Have It!',
}

def fix_figure(fig):
    """Fix a single figure to match Swift model"""
    
    # Map series to line
    series = fig.get('series', '')
    line = SERIES_TO_LINE.get(series, series)
    
    # Map status
    status = fig.get('status', 'want')
    swift_status = STATUS_MAP.get(status, status)
    
    # Rename imageString to imageName
    image = fig.get('imageString', '') or fig.get('imageName', '')
    
    return {
        'id': fig.get('id', ''),
        'name': fig.get('name', ''),
        'line': line,
        'wave': fig.get('wave'),
        'imageName': image,
        'status': swift_status,
        'notes': fig.get('notes', ''),
        'isFavorite': fig.get('isFavorite', False),
        'dateAdded': fig.get('dateAdded', ''),
        'year': fig.get('year'),
    }


def main():
    print(f"Loading {JSON_FILE}...")
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        figures = json.load(f)
    
    print(f"Loaded {len(figures)} figures")
    
    # Fix each figure
    fixed = [fix_figure(f) for f in figures]
    
    # Verify the fix
    print("\nSample fixed figure:")
    print(json.dumps(fixed[0], indent=2))
    
    # Count by line
    print("\nFigures by line:")
    lines = {}
    for f in fixed:
        line = f.get('line', 'unknown')
        lines[line] = lines.get(line, 0) + 1
    for line, count in sorted(lines.items()):
        print(f"  {line}: {count}")
    
    # Save
    print(f"\nSaving to {JSON_FILE}...")
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(fixed, f, indent=2)
    
    print("Done!")


if __name__ == '__main__':
    main()
