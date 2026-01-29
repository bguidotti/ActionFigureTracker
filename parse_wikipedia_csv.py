#!/usr/bin/env python3
"""
Parse the Wikipedia DC Multiverse CSV and create clean JSON

CSV Structure:
- Column A (Release): Category headers OR release dates (Q1 2020) OR empty
- Column B (Figure): Figure name
- Column C (Accessories): List of accessories
- Column D (Description): Version description to append to name

Output: Clean JSON with figures having:
- name: "Figure Name, Description" (e.g., "Batman, Detective Comics #1000 version")
- series: "dc-multiverse" or "dc-page-punchers"
- wave: The release date (Q1 2020, etc.)
- category: "Standard figures", "Gold Label", "Build-A", etc.
- accessories: List of accessories
- status: "want" (default)
- dateAdded: Generated from wave
"""

import csv
import json
import re
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uuid

sys.stdout.reconfigure(line_buffering=True)

CSV_FILE = r'c:\Code\ActionFigureTracker\wikipedia_list.csv'
JSON_FILE = r'c:\Code\ActionFigureTracker\Models\all_figures.json'


def parse_wave_to_date(wave: str) -> str:
    """Convert wave like 'Q1 2020' to a date string"""
    if not wave:
        return datetime.now().isoformat()
    
    wave = wave.strip()
    
    # Pattern: Q1 2020, Q2 2021, etc.
    q_match = re.match(r'Q(\d)\s*(\d{4})', wave)
    if q_match:
        quarter = int(q_match.group(1))
        year = int(q_match.group(2))
        month = (quarter - 1) * 3 + 1  # Q1=Jan, Q2=Apr, Q3=Jul, Q4=Oct
        return datetime(year, month, 1).isoformat()
    
    # Pattern: Fall 2020, Spring 2021, etc.
    season_match = re.match(r'(Fall|Spring|Summer|Winter)\s*(\d{4})', wave, re.IGNORECASE)
    if season_match:
        season = season_match.group(1).lower()
        year = int(season_match.group(2))
        month_map = {'spring': 3, 'summer': 6, 'fall': 9, 'winter': 12}
        month = month_map.get(season, 1)
        return datetime(year, month, 1).isoformat()
    
    # Pattern: just a year like 2020
    year_match = re.match(r'^(\d{4})$', wave)
    if year_match:
        return datetime(int(year_match.group(1)), 1, 1).isoformat()
    
    # Default
    return datetime.now().isoformat()


def parse_wave_to_year(wave: str) -> Optional[int]:
    """Extract year from wave string"""
    if not wave:
        return None
    match = re.search(r'(\d{4})', wave)
    if match:
        return int(match.group(1))
    return None


def is_category_header(text: str) -> bool:
    """Check if this row is a category header"""
    if not text:
        return False
    text = text.strip().lower()
    category_keywords = [
        'standard figures', 'deluxe', 'mega figures', 'gold label',
        'build-a', 'vehicles', 'theatrical', 'page punchers',
        'single figures', 'digital', 'mcfarlane figures', 'mcfarlane toys'
    ]
    return any(kw in text for kw in category_keywords)


def is_release_date(text: str) -> bool:
    """Check if this is a release date"""
    if not text:
        return False
    text = text.strip()
    # Q1 2020, Fall 2020, etc.
    return bool(re.match(r'^(Q\d|Fall|Spring|Summer|Winter|\d{4})', text, re.IGNORECASE))


def clean_text(text: str) -> str:
    """Clean up text by removing extra whitespace and quotes"""
    if not text:
        return ''
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)  # Collapse whitespace
    text = re.sub(r'^["\']|["\']$', '', text)  # Remove surrounding quotes
    return text


def create_figure_name(name: str, description: str) -> str:
    """Create full figure name by combining name and description"""
    name = clean_text(name)
    description = clean_text(description)
    
    if not name:
        return description or "Unknown Figure"
    
    if not description:
        return name
    
    # Check if description already contains "version" type info
    # or is a variant description
    if any(kw in description.lower() for kw in ['version', 'variant', 'edition', 'redeco', 'retool']):
        # Just append with comma
        return f"{name} ({description})"
    else:
        return f"{name} - {description}"


def parse_accessories(acc_text: str) -> List[str]:
    """Parse accessories string into list"""
    if not acc_text:
        return []
    
    acc_text = clean_text(acc_text)
    
    # Split by comma first
    parts = [p.strip() for p in acc_text.split(',')]
    
    # Filter out non-accessory items
    skip_patterns = [
        r'^display stand$',
        r'^art card$',
        r'^photo card$',
        r'^toy photo$',
        r'^artist proof$',
        r'^cgi card$',
        r'foil.*card',
    ]
    
    # Known artist names to filter out (these appear in "and X art card" patterns)
    artist_names = [
        'jim lee', 'bruce timm', 'todd mcfarlane', 'alex ross', 'greg capullo',
        'jason fabok', 'jorge jimenez', 'sean gordon murphy', 'david finch',
        'patrick gleason', 'dan jurgens', 'tony daniel', 'jim balent',
        'terry dodson', 'stephen amell', 'gal gadot', 'ben affleck',
        'henry cavill', 'ezra miller', 'ray fisher', 'jason momoa',
        'dwayne johnson', 'kaare andrews', 'scott williams', 'alex sinclair',
        'joe bennett', 'jack jadson', 'eddy barrows', 'jonboy meyers',
        'riccardo federici', 'dave johnson', 'karl kerschl', 'glen murakami',
        'barry kitson', 'jonathan glapion', 'sandu florea', 'tomeu morey'
    ]
    
    accessories = []
    for part in parts:
        part = part.strip()
        if not part or len(part) < 2:
            continue
        
        part_lower = part.lower()
        
        # Skip if matches skip patterns
        if any(re.search(pattern, part_lower) for pattern in skip_patterns):
            continue
        
        # Skip if it's just "and" followed by an artist name
        if part_lower.startswith('and '):
            rest = part_lower[4:].strip()
            if any(name in rest for name in artist_names):
                continue
        
        # Skip if it's just an artist name
        if any(part_lower == name or part_lower.startswith(name + ' ') for name in artist_names):
            continue
        
        # Clean up leading "and"
        if part.lower().startswith('and '):
            part = part[4:].strip()
        
        # Remove trailing "and [artist name]" patterns
        # e.g., "flight stand and Jim Lee" -> "flight stand"
        and_match = re.search(r'\s+and\s+[A-Z][a-z]+', part)
        if and_match:
            # Check if what follows "and" is an artist name
            after_and = part[and_match.start():].lower()
            if any(name in after_and for name in artist_names):
                part = part[:and_match.start()].strip()
        
        if part and len(part) > 1:
            accessories.append(part)
    
    return accessories


def main():
    print(f"Reading CSV from {CSV_FILE}...")
    
    figures = []
    current_category = "Standard figures"
    current_wave = ""
    current_series = "dc-multiverse"
    row_index = 0
    page_punchers_format = False  # Track if we're in Page Punchers section with different columns
    
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        
        for row in reader:
            row_index += 1
            
            # Pad row to at least 4 columns
            while len(row) < 4:
                row.append('')
            
            col_a = clean_text(row[0])  # Release/Category
            col_b = clean_text(row[1])  # Figure name
            col_c = clean_text(row[2])  # Accessories
            col_d = clean_text(row[3])  # Description
            
            # Skip empty rows
            if not col_a and not col_b and not col_c and not col_d:
                continue
            
            # Check for section headers
            # Explicitly exclude Mattel (blue box 2016–2019) — only McFarlane wanted
            if 'mattel' in col_a.lower() and 'mcfarlane' not in col_a.lower():
                current_series = "_exclude_mattel"
                continue
            
            if 'page punchers' in col_a.lower():
                current_series = "dc-page-punchers"
                current_category = "Page Punchers"
                page_punchers_format = True
                print(f"  Switched to series: {current_series}")
                continue
            
            if 'mcfarlane figures' in col_a.lower() and 'page punchers' not in col_a.lower():
                current_series = "dc-multiverse"
                page_punchers_format = False
                print(f"  Switched to series: {current_series}")
                continue
            
            # Check for category headers
            if is_category_header(col_a) and not col_b:
                current_category = col_a.strip()
                print(f"  Category: {current_category}")
                continue
            
            # Check for release date
            if is_release_date(col_a):
                current_wave = col_a.strip()
                # If there's also a figure name, process this row
                if not col_b:
                    continue
            
            # Skip header rows
            if col_b.lower() in ['figure', 'release', 'name']:
                continue
            
            # Handle Page Punchers format: Wave, Release, Figure, Accessories, Description
            if page_punchers_format and current_series == "dc-page-punchers":
                # Pad to at least 5 columns
                while len(row) < 5:
                    row.append('')
                
                pp_wave = clean_text(row[0])  # Wave (Wave 1, Wave 2, etc.)
                pp_release = clean_text(row[1])  # Release date (Summer 2022, etc.)
                pp_figure = clean_text(row[2])  # Figure name
                pp_accessories = clean_text(row[3])  # Accessories
                pp_description = clean_text(row[4])  # Description
                
                # Skip header row
                if pp_wave.lower() == 'wave' or pp_release.lower() == 'release':
                    continue
                
                # Update wave from release column if present
                if is_release_date(pp_release):
                    current_wave = pp_release
                elif is_release_date(pp_wave):
                    # Sometimes Wave column has the date
                    current_wave = pp_wave
                
                # Skip if no figure name
                if not pp_figure:
                    # Could be a variant row
                    if pp_description:
                        # Skip accessory-only descriptions
                        if any(kw in pp_description.lower() for kw in ['art card', 'display stand', 'comic']):
                            continue
                        if figures and figures[-1]['series'] == 'dc-page-punchers':
                            base_name = figures[-1]['name'].split(' (')[0]
                            variant_name = f"{base_name} ({pp_description})"
                            acc_list = parse_accessories(pp_accessories)
                            figure = {
                                'id': str(uuid.uuid4()),
                                'name': variant_name,
                                'series': current_series,
                                'wave': current_wave,
                                'category': current_category,
                                'year': parse_wave_to_year(current_wave),
                                'accessories': ', '.join(acc_list) if acc_list else '',
                                'status': 'want',
                                'isFavorite': False,
                                'isPlatinum': 'platinum' in pp_description.lower(),
                                'notes': '',
                                'imageString': '',
                                'dateAdded': parse_wave_to_date(current_wave)
                            }
                            if current_series != "_exclude_mattel":
                                figures.append(figure)
                    continue
                
                # Create figure: every row must have a disambiguating description (no bare character names)
                pp_desc = pp_description or current_category or current_wave or (
                    "DC Multiverse" if current_series in ("dc-multiverse", "dc-page-punchers") else "Figure"
                )
                full_name = create_figure_name(pp_figure, pp_desc)
                
                # Skip parsing artifacts
                skip_keywords = ['art card', 'photo card', 'display stand and', 'accessories']
                if any(kw in full_name.lower() for kw in skip_keywords):
                    continue
                
                acc_list = parse_accessories(pp_accessories)
                figure = {
                    'id': str(uuid.uuid4()),
                    'name': full_name,
                    'series': current_series,
                    'wave': current_wave,
                    'category': current_category,
                    'year': parse_wave_to_year(current_wave),
                    'accessories': ', '.join(acc_list) if acc_list else '',
                    'status': 'want',
                    'isFavorite': False,
                    'isPlatinum': 'platinum' in pp_description.lower() if pp_description else False,
                    'notes': '',
                    'imageString': '',
                    'dateAdded': parse_wave_to_date(current_wave)
                }
                if current_series != "_exclude_mattel":
                    figures.append(figure)
                continue
            
            # Skip empty figure names (unless continuing from previous)
            if not col_b and not col_d:
                continue
            
            # This is a figure row
            # If col_b is empty but col_d has content, it's a variant of previous figure
            if not col_b and col_d:
                # This is a variant - use description as the distinguishing factor
                # Skip if it looks like an accessory list, not a figure
                skip_keywords = ['art card', 'photo card', 'display stand', 'eskrima', 'batmobile piece']
                if any(kw in col_d.lower() for kw in skip_keywords):
                    continue
                
                # Skip variants that are just chase/platinum editions unless they have unique names
                if 'chase' in col_d.lower() or 'platinum edition' in col_d.lower():
                    # Still create an entry but mark it as platinum
                    if figures:
                        base_name = figures[-1]['name'].split(' (')[0]
                        variant_name = f"{base_name} ({col_d})"
                        is_platinum = True
                    else:
                        continue
                else:
                    # Skip if it's just a description without a real figure name
                    if col_d.startswith(('Redeco', 'Retool', 'Same as', 'variant', 'Blue', 'Gold', 'Bronze')):
                        continue
                    variant_name = col_d
                    is_platinum = False
                
                acc_list = parse_accessories(col_c)
                # Every figure must have a disambiguating description (no bare character names)
                variant_desc = col_d or current_category or current_wave or (
                    "DC Multiverse" if current_series in ("dc-multiverse", "dc-page-punchers") else "Figure"
                )
                figure = {
                    'id': str(uuid.uuid4()),
                    'name': variant_name if not col_b else create_figure_name(col_b, variant_desc),
                    'series': current_series,
                    'wave': current_wave,
                    'category': current_category,
                    'year': parse_wave_to_year(current_wave),
                    'accessories': ', '.join(acc_list) if acc_list else '',
                    'status': 'want',
                    'isFavorite': False,
                    'isPlatinum': 'platinum' in col_d.lower() if col_d else False,
                    'notes': '',
                    'imageString': '',
                    'dateAdded': parse_wave_to_date(current_wave)
                }
                if current_series != "_exclude_mattel":
                    figures.append(figure)
                continue
            
            # Regular figure entry: every row must have a disambiguating description (no bare character names)
            description_for_name = col_d or current_category or current_wave or (
                "DC Multiverse" if current_series in ("dc-multiverse", "dc-page-punchers") else "Figure"
            )
            full_name = create_figure_name(col_b, description_for_name)
            is_platinum = 'platinum' in (col_d or '').lower() if col_d else False
            
            # Skip entries that are clearly not figure names (parsing artifacts)
            skip_keywords = [
                'art card', 'photo card', 'display stand and', 'accessories',
                'eskrima sticks,', 'knife,', 'sword,', 'alternate hands,',
                'flight stand and', 'batmobile piece', '2 alternate hands,',
                'stand and'
            ]
            if any(kw in full_name.lower() for kw in skip_keywords):
                continue
            
            acc_list = parse_accessories(col_c)
            figure = {
                'id': str(uuid.uuid4()),
                'name': full_name,
                'series': current_series,
                'wave': current_wave,
                'category': current_category,
                'year': parse_wave_to_year(current_wave),
                'accessories': ', '.join(acc_list) if acc_list else '',
                'status': 'want',
                'isFavorite': False,
                'isPlatinum': is_platinum,
                'notes': '',
                'imageString': '',
                'dateAdded': parse_wave_to_date(current_wave)
            }
            if current_series != "_exclude_mattel":
                figures.append(figure)
    
    print(f"\nParsed {len(figures)} figures total")
    
    # Count by series
    series_counts = {}
    for f in figures:
        s = f['series']
        series_counts[s] = series_counts.get(s, 0) + 1
    
    print("\nBy series:")
    for s, c in sorted(series_counts.items()):
        print(f"  {s}: {c}")
    
    # Count by category
    cat_counts = {}
    for f in figures:
        c = f['category']
        cat_counts[c] = cat_counts.get(c, 0) + 1
    
    print("\nBy category:")
    for c, count in sorted(cat_counts.items()):
        print(f"  {c}: {count}")
    
    # Show sample figures
    print("\nSample figures (first 10):")
    for f in figures[:10]:
        print(f"  - {f['name']}")
        if f['accessories']:
            acc_preview = f['accessories'][:80] + '...' if len(f['accessories']) > 80 else f['accessories']
            print(f"    Accessories: {acc_preview}")
    
    # Load existing JSON to preserve other series
    print(f"\nLoading existing JSON from {JSON_FILE}...")
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        print(f"  Loaded {len(existing)} existing figures")
    except:
        existing = []
        print("  No existing file or error loading")
    
    # Keep non-DC figures from existing
    other_figures = [f for f in existing if f.get('series') not in ['dc-multiverse', 'dc-page-punchers']]
    print(f"  Keeping {len(other_figures)} non-DC figures")
    
    # Combine: new DC figures + other existing figures
    all_figures = figures + other_figures
    
    print(f"\nTotal figures to save: {len(all_figures)}")
    
    # Save
    print(f"Saving to {JSON_FILE}...")
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_figures, f, indent=2)
    
    print("Done!")


if __name__ == '__main__':
    main()
