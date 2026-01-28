#!/usr/bin/env python3
"""
Fetch images from the ImageServer for figures missing images
"""

import json
import requests
import sys
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(line_buffering=True)

JSON_FILE = r'c:\Code\ActionFigureTracker\Models\all_figures.json'
API_URL = 'http://localhost:5050/api/search'

# Map series to line names for the API
SERIES_TO_LINE = {
    'dc-multiverse': 'DC Multiverse',
    'dc-page-punchers': 'DC Page Punchers',
    'dc-super-powers': 'DC Super Powers',
    'dc-retro': 'DC Retro',
}

def get_search_query(name, series):
    """Create search query from figure name"""
    # Remove parenthetical version info for cleaner search
    query = re.sub(r'\s*\([^)]*\)', '', name)
    query = query.split(' - ')[0].strip()
    
    # Add line context
    if series == 'dc-page-punchers':
        query += ' Page Punchers'
    elif series == 'dc-multiverse':
        query += ' Multiverse'
    elif series == 'dc-super-powers':
        query += ' Super Powers'
    
    return query

def search_image(name, series):
    """Search for an image using the API"""
    query = get_search_query(name, series)
    line = SERIES_TO_LINE.get(series, '')
    
    try:
        params = {
            'q': query,
            'sources': 'actionfigure411',
            'line': line
        }
        response = requests.get(API_URL, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                # Return the first result's URL
                return data['results'][0]['url']
    except Exception as e:
        pass
    
    return None

def main():
    print("Loading figures...")
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        figures = json.load(f)
    
    # Find figures needing images (only DC lines)
    dc_series = ['dc-multiverse', 'dc-page-punchers', 'dc-super-powers', 'dc-retro']
    missing = [f for f in figures if f['series'] in dc_series and not f.get('imageString', '').startswith('http')]
    
    print(f"Found {len(missing)} DC figures missing images")
    
    if not missing:
        print("All DC figures have images!")
        return
    
    # Test API connection
    print("\nTesting API connection...")
    try:
        response = requests.get('http://localhost:5050/api/health', timeout=5)
        if response.status_code != 200:
            print("ERROR: ImageServer not responding. Start it with: python ImageServer/app.py")
            return
    except:
        print("ERROR: Cannot connect to ImageServer at localhost:5050")
        print("Start it with: cd ImageServer && python app.py")
        return
    
    print("API connected!")
    
    # Fetch images
    print(f"\nFetching images for {len(missing)} figures...")
    found = 0
    
    for i, fig in enumerate(missing):
        name = fig['name']
        series = fig['series']
        
        img_url = search_image(name, series)
        if img_url:
            # Find and update the figure in the main list
            for f in figures:
                if f['id'] == fig['id']:
                    f['imageString'] = img_url
                    found += 1
                    break
            print(f"  [{i+1}/{len(missing)}] Found: {name[:40]}...")
        else:
            print(f"  [{i+1}/{len(missing)}] Not found: {name[:40]}...")
        
        # Rate limit
        time.sleep(0.1)
        
        # Progress update every 50
        if (i + 1) % 50 == 0:
            print(f"  Progress: {i+1}/{len(missing)}, found {found} images")
    
    print(f"\nFound images for {found}/{len(missing)} figures")
    
    # Save
    print(f"Saving to {JSON_FILE}...")
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(figures, f, indent=2)
    
    print("Done!")

if __name__ == '__main__':
    main()
