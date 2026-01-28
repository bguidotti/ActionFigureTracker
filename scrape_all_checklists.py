#!/usr/bin/env python3
"""
Scrape all DC action figure checklists from actionfigure411.com
and update all_figures.json with correct order and data.
"""

import json
import re
import time
import urllib.request
from typing import Dict, List, Optional
from collections import defaultdict

# URLs to scrape
CHECKLIST_URLS = {
    'dc-multiverse': 'https://www.actionfigure411.com/dc/multiverse-checklist.php',
    'dc-super-powers': 'https://www.actionfigure411.com/dc/mcfarlane-super-powers-checklist.php',
    'dc-retro': 'https://www.actionfigure411.com/dc/retro-66-checklist.php',
    'dc-page-punchers': 'https://www.actionfigure411.com/dc/page-punchers-checklist.php',
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

JSON_FILE = r'c:\Code\ActionFigureTracker\Models\all_figures.json'


def fetch_url(url: str) -> Optional[str]:
    """Fetch a URL and return its content as string"""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return None


def parse_checklist_table(html: str) -> List[Dict]:
    """
    Parse the checklist table from HTML
    Returns list of figures with: name, wave, year, retail
    Handles multiple tables on the page (Action Figures, Vehicles, etc.)
    """
    figures = []
    
    # Find all tables - look for table tags with checklist data
    # Skip header rows and find data rows
    # Pattern: <tr> with <td> containing links to figure pages
    
    # First, find all table rows that contain figure links
    # Look for rows with <a href=".../action-figures/..."> or similar patterns
    row_pattern = r'<tr[^>]*>(.*?)</tr>'
    rows = re.findall(row_pattern, html, re.DOTALL | re.IGNORECASE)
    
    header_keywords = ['name', 'wave', 'year', 'retail', 'action figures checklist', 
                      'vehicles and playsets', 'action figure packs', 'the new adventures',
                      'super friends', 'mattel checklist', 'mcfarlane checklist']
    
    for row in rows:
        # Skip header rows
        row_lower = row.lower()
        if any(keyword in row_lower for keyword in header_keywords):
            continue
        
        # Extract all table cells
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
        
        # Need at least: checkbox, name, wave, year (4 cells)
        if len(cells) < 4:
            continue
        
        # The table structure has:
        # Cell 0: Checkbox (ignore)
        # Cell 1: Name (in <h3><a> structure)
        # Cell 2: Wave
        # Cell 3: Year
        # Cell 4: Retail
        
        # Skip if we don't have enough cells (need at least checkbox + name + wave + year)
        if len(cells) < 4:
            continue
        
        # Extract name from second cell (index 1)
        name_cell = cells[1]
        
        # Pattern: <h3><a href="...">Name</a></h3> or just <a href="...">Name</a>
        name_match = re.search(r'<a[^>]+href="[^"]*\.php"[^>]*>([^<]+)</a>', name_cell, re.IGNORECASE)
        
        if name_match:
            name = name_match.group(1).strip()
        else:
            # Try plain text, remove HTML tags
            name = re.sub(r'<[^>]+>', '', name_cell).strip()
        
        # Clean name - remove HTML entities and normalize
        name = name.replace('&amp;', '&').replace('&nbsp;', ' ').replace('&quot;', '"')
        name = name.replace('&apos;', "'").replace('&#39;', "'").replace('&lt;', '<').replace('&gt;', '>')
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Skip if empty or header row
        if not name or name.lower() in ['name', 'wave', 'year', 'retail', '']:
            continue
        
        # Parse remaining cells: wave, year, retail
        wave = None
        year = None
        retail = None
        
        # Wave is in third cell (index 2)
        if len(cells) >= 3:
            wave_cell = re.sub(r'<[^>]+>', '', cells[2]).strip()
            wave_cell = wave_cell.replace('&nbsp;', ' ').replace('&amp;', '&')
            if wave_cell and wave_cell.lower() not in ['wave', 'year', 'retail', '']:
                wave = wave_cell if wave_cell else None
        
        # Year is in fourth cell (index 3)
        if len(cells) >= 4:
            year_cell = re.sub(r'<[^>]+>', '', cells[3]).strip()
            year_cell = year_cell.replace('&nbsp;', ' ').replace('&amp;', '&')
            year_match = re.search(r'(\d{4})', year_cell)
            if year_match:
                try:
                    year = int(year_match.group(1))
                except ValueError:
                    year = None
        
        # Retail is in fifth cell (index 4)
        if len(cells) >= 5:
            retail_cell = re.sub(r'<[^>]+>', '', cells[4]).strip()
            retail_cell = retail_cell.replace('&nbsp;', ' ').replace('&amp;', '&')
            if retail_cell and retail_cell.lower() not in ['retail', '']:
                retail = retail_cell if retail_cell else None
        
        # Only add if we have at least a name
        if name:
            figures.append({
                'name': name,
                'wave': wave,
                'year': year,
                'retail': retail
            })
    
    return figures


def normalize_name(name: str) -> str:
    """Normalize a figure name for matching"""
    name = name.lower()
    # Remove HTML entities
    name = name.replace('&amp;', '&').replace('&nbsp;', ' ')
    # Remove extra whitespace
    name = re.sub(r'\s+', ' ', name)
    return name.strip()


def match_figure(scraped_fig: Dict, existing_figures: List[Dict]) -> Optional[Dict]:
    """Find matching figure in existing data"""
    scraped_name = normalize_name(scraped_fig['name'])
    
    # Try exact match first
    for fig in existing_figures:
        existing_name = normalize_name(fig.get('name', ''))
        if scraped_name == existing_name:
            return fig
    
    # Try fuzzy match (check if key words match)
    scraped_words = set(scraped_name.split())
    best_match = None
    best_score = 0
    
    for fig in existing_figures:
        existing_name = normalize_name(fig.get('name', ''))
        existing_words = set(existing_name.split())
        
        # Calculate overlap
        common = scraped_words & existing_words
        if len(common) >= 2:  # At least 2 words in common
            score = len(common) / max(len(scraped_words), len(existing_words))
            if score > best_score and score > 0.5:
                best_score = score
                best_match = fig
    
    return best_match


def update_figures_with_scraped_data(existing_figures: List[Dict], scraped_figures: Dict[str, List[Dict]]) -> List[Dict]:
    """
    Update existing figures with scraped data, maintaining order from checklists
    Returns updated list sorted by series, then by order from checklist
    """
    from datetime import datetime, timedelta
    
    # Create lookup by series
    figures_by_series = defaultdict(list)
    for fig in existing_figures:
        series = fig.get('series', 'dc-multiverse')
        figures_by_series[series].append(fig)
    
    updated_figures = []
    next_id = max((f.get('id', 0) for f in existing_figures), default=0) + 1
    
    # Integrate Page Punchers into Multiverse (as user requested)
    # Page Punchers should be added to Multiverse, maintaining their order
    if 'dc-page-punchers' in scraped_figures:
        if 'dc-multiverse' not in scraped_figures:
            scraped_figures['dc-multiverse'] = []
        # Add Page Punchers to the end of Multiverse list (they're already sorted oldest to newest)
        page_punchers_list = scraped_figures['dc-page-punchers']
        scraped_figures['dc-multiverse'].extend(page_punchers_list)
        # Sort Multiverse by year, then maintain relative order within each year
        # Create a stable sort key: (year, original_index)
        multiverse_with_indices = [(fig, idx) for idx, fig in enumerate(scraped_figures['dc-multiverse'])]
        multiverse_with_indices.sort(key=lambda x: (x[0].get('year') or 9999, x[1]))
        scraped_figures['dc-multiverse'] = [fig for fig, _ in multiverse_with_indices]
        del scraped_figures['dc-page-punchers']
    
    # Process each series in order
    series_order = ['dc-multiverse', 'dc-super-powers', 'dc-retro']
    
    for series in series_order:
        if series not in scraped_figures:
            # Add existing figures from this series that weren't scraped
            updated_figures.extend(figures_by_series.get(series, []))
            continue
        
        scraped_list = scraped_figures[series]
        print(f"\nProcessing {series}: {len(scraped_list)} figures from checklist")
        
        # Create a map of existing figures by normalized name
        existing_map = {}
        for fig in figures_by_series.get(series, []):
            key = normalize_name(fig.get('name', ''))
            if key not in existing_map:
                existing_map[key] = fig
        
        # Process scraped figures in order (they're already sorted oldest to newest)
        processed_ids = set()
        base_date = datetime(2020, 1, 1)  # Base date for ordering
        
        for idx, scraped in enumerate(scraped_list):
            name = scraped['name']
            normalized = normalize_name(name)
            
            # Try to find existing figure - check exact match first
            matched = existing_map.get(normalized)
            
            # If no exact match, try fuzzy matching (but be more careful)
            if not matched:
                for existing_name, existing_fig in existing_map.items():
                    # Check if names are very similar (allowing for minor differences)
                    if normalized in existing_name or existing_name in normalized:
                        # Additional check: make sure key words match
                        scraped_words = set(normalized.split())
                        existing_words = set(existing_name.split())
                        if len(scraped_words & existing_words) >= 2:  # At least 2 words in common
                            matched = existing_fig
                            break
            
            if matched and matched.get('id') not in processed_ids:
                # Update existing figure with scraped data
                matched['year'] = scraped['year']
                if scraped.get('wave'):
                    matched['wave'] = scraped['wave']
                if scraped.get('retail'):
                    matched['retail'] = scraped['retail']
                # Update dateAdded based on year and position to maintain checklist order
                if scraped['year']:
                    # Use year as base, add days based on position to maintain order
                    # This ensures figures are sorted correctly within each year
                    date_obj = datetime(scraped['year'], 1, 1) + timedelta(days=idx)
                    matched['dateAdded'] = date_obj.isoformat()
                else:
                    # If no year, use a default date but still maintain order
                    date_obj = datetime(2020, 1, 1) + timedelta(days=idx)
                    matched['dateAdded'] = date_obj.isoformat()
                updated_figures.append(matched)
                processed_ids.add(matched.get('id'))
            else:
                # New figure - create it
                if scraped['year']:
                    date_obj = datetime(scraped['year'], 1, 1) + timedelta(days=idx)
                else:
                    date_obj = datetime(2020, 1, 1) + timedelta(days=idx)
                new_fig = {
                    'id': next_id,
                    'name': name,
                    'series': series,
                    'imageString': matched.get('imageString', '') if matched else '',
                    'isCollected': matched.get('isCollected', False) if matched else False,
                    'year': scraped['year'],
                    'wave': scraped.get('wave'),
                    'retail': scraped.get('retail'),
                    'dateAdded': date_obj.isoformat()
                }
                updated_figures.append(new_fig)
                next_id += 1
                print(f"  New figure: {name}")
        
        # Add any existing figures from this series that weren't in the scraped list
        # (keep them at the end with a future date)
        for fig in figures_by_series.get(series, []):
            if fig.get('id') not in processed_ids:
                # Keep existing date or set to future
                if 'dateAdded' not in fig or not fig.get('dateAdded'):
                    fig['dateAdded'] = datetime(2099, 1, 1).isoformat()
                updated_figures.append(fig)
    
    # Add figures from other series that weren't processed
    processed_series = set(scraped_figures.keys())
    for series, figs in figures_by_series.items():
        if series not in processed_series:
            updated_figures.extend(figs)
    
    # Sort by series order, then by dateAdded (which reflects checklist order)
    series_order_map = {s: i for i, s in enumerate(series_order)}
    
    def sort_key(fig):
        series = fig.get('series', 'dc-multiverse')
        series_idx = series_order_map.get(series, 999)
        date_str = fig.get('dateAdded', '')
        try:
            date_val = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            date_val = datetime(2099, 1, 1)
        return (series_idx, date_val)
    
    updated_figures.sort(key=sort_key)
    
    return updated_figures


def main():
    print("Scraping actionfigure411.com checklists...")
    
    # Load existing data
    print(f"\nLoading existing data from {JSON_FILE}...")
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            existing_figures = json.load(f)
        print(f"Loaded {len(existing_figures)} existing figures")
    except Exception as e:
        print(f"Error loading JSON: {e}")
        existing_figures = []
    
    # Scrape each checklist
    scraped_data = {}
    
    for series, url in CHECKLIST_URLS.items():
        print(f"\n{'='*60}")
        print(f"Scraping {series}: {url}")
        print('='*60)
        
        html = fetch_url(url)
        if not html:
            print(f"  Failed to fetch {series}")
            continue
        
        # Debug: save first 5000 chars to see structure
        if series == 'dc-multiverse':
            with open(f'debug_{series}.html', 'w', encoding='utf-8') as f:
                f.write(html[:5000])
            print(f"  Saved sample HTML to debug_{series}.html")
        
        figures = parse_checklist_table(html)
        print(f"  Found {len(figures)} figures")
        
        if figures:
            scraped_data[series] = figures
            # Show first few as sample
            print(f"  Sample figures:")
            for fig in figures[:5]:
                print(f"    - {fig['name']} ({fig.get('year', 'N/A')}) - Wave: {fig.get('wave', 'N/A')}")
            if len(figures) > 5:
                print(f"    ... and {len(figures) - 5} more")
            
            # Show last few to verify ordering
            if len(figures) > 10:
                print(f"  Last few figures:")
                for fig in figures[-3:]:
                    print(f"    - {fig['name']} ({fig.get('year', 'N/A')}) - Wave: {fig.get('wave', 'N/A')}")
        else:
            print(f"  WARNING: No figures found for {series}!")
            # Save HTML for debugging
            debug_file = f'debug_{series}_no_figures.html'
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"  Saved HTML to {debug_file} for debugging")
        
        time.sleep(1)  # Be nice to the server
    
    # Update existing figures
    print(f"\n{'='*60}")
    print("Updating figures with scraped data...")
    print('='*60)
    
    updated_figures = update_figures_with_scraped_data(existing_figures, scraped_data)
    
    # Save updated data
    print(f"\nSaving updated data...")
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(updated_figures, f, indent=2)
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    print(f"Total figures: {len(updated_figures)}")
    for series in scraped_data.keys():
        count = sum(1 for f in updated_figures if f.get('series') == series)
        print(f"  {series}: {count} figures")
    print(f"\nData saved to {JSON_FILE}")


if __name__ == '__main__':
    main()
