#!/usr/bin/env python3
"""
Fix JSON to match DataLoader's RawFigure format
"""

import json
import sys

sys.stdout.reconfigure(line_buffering=True)

JSON_FILE = r'c:\Code\ActionFigureTracker\Models\all_figures.json'

# Map line values back to series format that DataLoader expects
LINE_TO_SERIES = {
    'DC Multiverse': 'dc-multiverse',
    'DC Super Powers': 'dc-super-powers',
    'DC Retro': 'dc-retro',
    'DC Direct': 'dc-direct',
    'Marvel Legends': 'marvel-legends',
    'MOTU Origins': 'masters-of-the-universe-origins',
    'MOTU Masterverse': 'masters-of-the-universe-masterverse',
    'Star Wars Black Series': 'star-wars-black-series',
}

def fix_figure(fig, index):
    """Fix a single figure to match RawFigure format"""
    
    # Get series from line or existing series
    line = fig.get('line', '')
    series = LINE_TO_SERIES.get(line, fig.get('series', 'dc-multiverse'))
    
    # Get image from imageName or imageString
    image = fig.get('imageName', '') or fig.get('imageString', '')
    
    # Convert status to isCollected
    status = fig.get('status', '')
    is_collected = status in ['have', 'I Have It!', True]
    
    return {
        'id': index + 1,  # Use sequential integer IDs
        'name': fig.get('name', ''),
        'series': series,
        'imageString': image,
        'isCollected': is_collected,
        'year': fig.get('year'),
        'wave': fig.get('wave'),
    }


def main():
    print(f"Loading {JSON_FILE}...")
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        figures = json.load(f)
    
    print(f"Loaded {len(figures)} figures")
    
    # Fix each figure
    fixed = [fix_figure(f, i) for i, f in enumerate(figures)]
    
    # Verify the fix
    print("\nSample fixed figure:")
    print(json.dumps(fixed[0], indent=2))
    
    # Count by series
    print("\nFigures by series:")
    series_counts = {}
    for f in fixed:
        s = f.get('series', 'unknown')
        series_counts[s] = series_counts.get(s, 0) + 1
    for s, count in sorted(series_counts.items()):
        print(f"  {s}: {count}")
    
    # Save
    print(f"\nSaving to {JSON_FILE}...")
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(fixed, f, indent=2)
    
    print("Done!")


if __name__ == '__main__':
    main()
