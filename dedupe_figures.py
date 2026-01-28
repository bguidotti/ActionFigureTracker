#!/usr/bin/env python3
"""
Deduplicate figures in all_figures.json

Priority for keeping entries:
1. Has actionfigure411.com image (largest/best quality)
2. Has legendsverse.com image
3. Has any other image
4. No image

For figures with same priority, keep the one with more metadata (wave, year, notes, etc.)
"""

import json
import sys
from collections import defaultdict
from typing import Dict, List, Any

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

JSON_FILE = r'c:\Code\ActionFigureTracker\Models\all_figures.json'


def get_image_priority(figure: Dict) -> int:
    """
    Return priority score for image source (higher = better)
    """
    image = figure.get('imageString', '') or ''
    
    if 'actionfigure411.com' in image:
        return 4  # Best - large images
    elif 'legendsverse.com' in image:
        return 2  # Medium - smaller images
    elif image and image != 'placeholder':
        return 1  # Some other image source
    else:
        return 0  # No image


def get_metadata_score(figure: Dict) -> int:
    """
    Return score based on how much metadata the figure has
    """
    score = 0
    
    if figure.get('wave'):
        score += 1
    if figure.get('year'):
        score += 1
    if figure.get('notes'):
        score += 1
    if figure.get('retail'):
        score += 1
    if figure.get('isFavorite'):
        score += 2  # User data is important
    if figure.get('status') == 'have':
        score += 3  # User marked as owned - very important!
    
    return score


def create_unique_key(figure: Dict) -> str:
    """
    Create a unique key for a figure based on name and series
    """
    name = figure.get('name', '').lower().strip()
    series = figure.get('series', '').lower().strip()
    return f"{series}::{name}"


def choose_best_figure(duplicates: List[Dict]) -> Dict:
    """
    Given a list of duplicate figures, choose the best one to keep
    """
    if len(duplicates) == 1:
        return duplicates[0]
    
    # Sort by: image priority (desc), metadata score (desc)
    sorted_figures = sorted(
        duplicates,
        key=lambda f: (get_image_priority(f), get_metadata_score(f)),
        reverse=True
    )
    
    best = sorted_figures[0]
    
    # Merge useful data from other duplicates into the best one
    for other in sorted_figures[1:]:
        # Keep user data if present in any duplicate
        if other.get('isFavorite') and not best.get('isFavorite'):
            best['isFavorite'] = True
        if other.get('status') == 'have' and best.get('status') != 'have':
            best['status'] = 'have'
        if other.get('notes') and not best.get('notes'):
            best['notes'] = other['notes']
        # Keep metadata if missing
        if other.get('wave') and not best.get('wave'):
            best['wave'] = other['wave']
        if other.get('year') and not best.get('year'):
            best['year'] = other['year']
        if other.get('retail') and not best.get('retail'):
            best['retail'] = other['retail']
    
    return best


def main():
    print(f"Loading figures from {JSON_FILE}...")
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        all_figures = json.load(f)
    
    print(f"Total figures before dedup: {len(all_figures)}")
    
    # Group figures by unique key
    groups: Dict[str, List[Dict]] = defaultdict(list)
    for figure in all_figures:
        key = create_unique_key(figure)
        groups[key].append(figure)
    
    print(f"Unique figure keys: {len(groups)}")
    
    # Find duplicates
    duplicates = {k: v for k, v in groups.items() if len(v) > 1}
    print(f"Keys with duplicates: {len(duplicates)}")
    
    # Show some examples of duplicates
    print("\nSample duplicates:")
    sample_count = 0
    for key, figs in sorted(duplicates.items(), key=lambda x: -len(x[1])):
        if sample_count >= 10:
            break
        print(f"  '{key}': {len(figs)} copies")
        for fig in figs[:3]:
            img = fig.get('imageString', '')[:50] if fig.get('imageString') else 'none'
            print(f"    - img: {img}...")
        sample_count += 1
    
    # Deduplicate - keep best entry for each key
    print("\nDeduplicating...")
    deduped = []
    for key, figures in groups.items():
        best = choose_best_figure(figures)
        deduped.append(best)
    
    print(f"Total figures after dedup: {len(deduped)}")
    print(f"Removed {len(all_figures) - len(deduped)} duplicates")
    
    # Sort by series then by dateAdded (or name if no date)
    deduped.sort(key=lambda f: (
        f.get('series', ''),
        f.get('dateAdded', '2000-01-01')
    ))
    
    # Count by series
    print("\nFigures by series:")
    series_counts = defaultdict(int)
    for fig in deduped:
        series_counts[fig.get('series', 'unknown')] += 1
    for series, count in sorted(series_counts.items()):
        print(f"  {series}: {count}")
    
    # Count image sources
    print("\nImage sources:")
    img_counts = defaultdict(int)
    for fig in deduped:
        img = fig.get('imageString', '') or ''
        if 'actionfigure411.com' in img:
            img_counts['actionfigure411'] += 1
        elif 'legendsverse.com' in img:
            img_counts['legendsverse'] += 1
        elif img and img != 'placeholder':
            img_counts['other'] += 1
        else:
            img_counts['none'] += 1
    for source, count in sorted(img_counts.items()):
        print(f"  {source}: {count}")
    
    # Save
    print(f"\nSaving to {JSON_FILE}...")
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(deduped, f, indent=2)
    
    print("Done!")


if __name__ == '__main__':
    main()
