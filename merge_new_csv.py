#!/usr/bin/env python3
"""
Merge new comprehensive CSV data into all_figures.json
Reads from DC_Multiverse.csv file
"""

import json
import csv
import re
import os
import sys
from typing import Dict, List, Optional

def normalize_name(name: str) -> str:
    """Normalize figure name for comparison"""
    name = re.sub(r'\s+', ' ', name.strip())
    name = name.replace(' (Chase)', '').replace(' Platinum', '').replace(' Platinum (Chase)', '')
    name = name.replace(':', ' ').replace('(', ' ').replace(')', ' ')
    name = re.sub(r'\s+', ' ', name)
    return name.lower().strip()

def normalize_series(series: str) -> str:
    """Convert series name to JSON format"""
    series_map = {
        'DC Multiverse': 'dc-multiverse',
        'DC Super Powers': 'dc-super-powers',
        'DC Retro': 'dc-retro',
        'DC Direct': 'dc-direct',
        'MOTU Origins': 'masters-of-the-universe-origins',
        'MOTU Masterverse': 'masters-of-the-universe-masterverse',
        'Marvel Legends': 'marvel-legends',
        'Star Wars Black Series': 'star-wars-black-series',
        'Page Punchers': 'dc-multiverse'  # Page Punchers are DC Multiverse sub-line
    }
    return series_map.get(series, series.lower().replace(' ', '-'))

def load_existing_json(filepath: str) -> List[Dict]:
    """Load existing JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"WARNING: File not found: {filepath}")
        return []
    except json.JSONDecodeError as e:
        print(f"ERROR: Error parsing JSON: {e}")
        return []

def find_existing_figure(figures: List[Dict], csv_name: str) -> Optional[Dict]:
    """Find existing figure by normalized name with fuzzy matching"""
    normalized_csv = normalize_name(csv_name)
    
    # Try exact match first
    for fig in figures:
        fig_name = normalize_name(fig.get('name', ''))
        if fig_name == normalized_csv:
            return fig
    
    # Try partial match
    csv_parts = set(normalized_csv.split())
    for fig in figures:
        fig_name = normalize_name(fig.get('name', ''))
        fig_parts = set(fig_name.split())
        if len(csv_parts) > 0 and len(fig_parts) > 0:
            overlap = len(csv_parts & fig_parts) / max(len(csv_parts), len(fig_parts))
            if overlap > 0.7:
                return fig
    
    return None

def get_next_id(figures: List[Dict]) -> int:
    """Get the next available ID"""
    if not figures:
        return 1
    max_id = max((fig.get('id', 0) for fig in figures), default=0)
    return max_id + 1

def merge_data(existing_figures: List[Dict], csv_data: List[Dict]) -> List[Dict]:
    """Merge CSV data into existing figures"""
    updated_count = 0
    new_count = 0
    
    for csv_row in csv_data:
        # Skip header row if present
        if csv_row.get('Year') == 'Year' or csv_row.get('Name') == 'Name':
            continue
            
        # Parse year safely
        year_str = csv_row.get('Year', '').strip()
        try:
            year = int(year_str) if year_str else None
        except (ValueError, TypeError):
            year = None
            
        wave = csv_row.get('Wave', '').strip() if csv_row.get('Wave') else None
        name = csv_row.get('Name', '').strip() if csv_row.get('Name') else ''
        
        # Handle different CSV formats - check for 'Series' or 'DC Multiverse' column
        series_str = csv_row.get('Series', '').strip() if csv_row.get('Series') else ''
        if not series_str:
            # Try 'DC Multiverse' column (might be empty, default to DC Multiverse)
            series_str = csv_row.get('DC Multiverse', '').strip()
            if not series_str:
                series_str = 'DC Multiverse'  # Default if not specified
        
        if not name or not year:
            continue
        
        series = normalize_series(series_str)
        existing = find_existing_figure(existing_figures, name)
        
        if existing:
            updated = False
            if not existing.get('series') or existing.get('series') == 'dc-multiverse':
                existing['series'] = series
                updated = True
            if 'year' not in existing:
                existing['year'] = year
                updated = True
            if 'wave' not in existing and wave:
                existing['wave'] = wave
                updated = True
            elif wave and existing.get('wave') != wave:
                # Update wave if different (might be more specific)
                existing['wave'] = wave
                updated = True
            if updated:
                updated_count += 1
        else:
            new_id = get_next_id(existing_figures)
            new_fig = {
                'id': new_id,
                'name': name,
                'series': series,
                'imageString': '',
                'isCollected': False,
                'year': year
            }
            if wave:
                new_fig['wave'] = wave
            existing_figures.append(new_fig)
            new_count += 1
    
    def sort_key(fig: Dict) -> tuple:
        year = fig.get('year', 9999)
        name = fig.get('name', '').lower()
        return (year, name)
    
    existing_figures.sort(key=sort_key)
    
    print(f"   Updated {updated_count} existing figures")
    print(f"   Added {new_count} new figures")
    
    return existing_figures

def main():
    # CSV file paths to try
    csv_file_paths = [
        r'\\tsclient\Downloads\DC_Multiverse.csv',
        r'C:\Users\guido\Downloads\DC_Multiverse.csv',
        r'DC_Multiverse.csv',
        os.path.join(os.path.dirname(__file__), 'DC_Multiverse.csv')
    ]
    
    if len(sys.argv) > 1:
        csv_file_paths.insert(0, sys.argv[1])
    
    csv_file_path = None
    for path in csv_file_paths:
        if os.path.exists(path):
            csv_file_path = path
            break
    
    if not csv_file_path:
        print("ERROR: Could not find DC_Multiverse.csv file")
        print("Tried paths:")
        for path in csv_file_paths:
            print(f"  - {path}")
        print("\nPlease provide the CSV file path as an argument or place it in the current directory.")
        return
    
    json_file = r'c:\Code\ActionFigureTracker\Models\all_figures.json'
    backup_file = json_file + '.backup'
    
    print(f"Loading CSV from: {csv_file_path}")
    with open(csv_file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        csv_data = list(reader)
    
    print(f"   Found {len(csv_data)} CSV entries")
    if csv_data:
        print(f"   Sample row: {csv_data[0]}")
        print(f"   Columns: {list(csv_data[0].keys())}")
    
    print("Loading existing JSON...")
    existing_figures = load_existing_json(json_file)
    print(f"   Found {len(existing_figures)} existing figures")
    
    print("Merging data...")
    merged_figures = merge_data(existing_figures, csv_data)
    
    print(f"\nMerge complete!")
    print(f"   Total figures: {len(merged_figures)}")
    
    print(f"\nCreating backup...")
    import shutil
    shutil.copy2(json_file, backup_file)
    print(f"   Backup saved to: {backup_file}")
    
    print(f"\nWriting merged JSON...")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(merged_figures, f, indent=2, ensure_ascii=False)
    
    print(f"Done! Merged data saved to: {json_file}")

if __name__ == '__main__':
    main()
