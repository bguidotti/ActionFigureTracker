#!/usr/bin/env python3
"""
Find image URLs for all figures missing images
Searches actionfigure411.com and legendsverse.com
Includes rate limiting and progress saving
"""

import json
import re
import time
import urllib.parse
from typing import Optional, List, Dict
import os

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_REQUIRED_LIBS = True
except ImportError:
    HAS_REQUIRED_LIBS = False
    print("ERROR: Missing required libraries.")
    print("Please install them with:")
    print("  pip install requests beautifulsoup4")
    print()
    exit(1)

# Configuration
JSON_FILE = r'c:\Code\ActionFigureTracker\Models\all_figures.json'
PROGRESS_FILE = r'c:\Code\ActionFigureTracker\image_search_progress.json'
DELAY_BETWEEN_REQUESTS = 2  # seconds - be respectful to servers
MAX_RETRIES = 3

def normalize_name(name: str) -> str:
    """Normalize figure name for search"""
    name = re.sub(r'\s+', ' ', name.strip())
    name = name.replace(':', ' ').replace('(', ' ').replace(')', ' ')
    name = re.sub(r'\s+', ' ', name)
    return name.lower().strip()

def create_search_url(figure_name: str, site: str = "actionfigure411") -> str:
    """Create search URL for actionfigure411.com"""
    if site == "actionfigure411":
        # Try to construct direct page URL from name
        slug = figure_name.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        slug = slug.strip('-')
        return f"https://www.actionfigure411.com/dc/multiverse/mcfarlane/{slug}"
    return None

def search_actionfigure411_direct(figure_name: str) -> Optional[str]:
    """
    Try to find figure page directly on actionfigure411.com
    Returns image URL if found
    """
    try:
        # Create potential URL
        slug = figure_name.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        slug = slug.strip('-')
        
        # Try common URL patterns
        potential_urls = [
            f"https://www.actionfigure411.com/dc/multiverse/mcfarlane/{slug}",
            f"https://www.actionfigure411.com/dc/multiverse/mcfarlane/{slug}-",
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        for base_url in potential_urls:
            # Try with common ID patterns (we'll search the page for the actual ID)
            search_url = f"https://www.actionfigure411.com/dc/multiverse-visual-guide.php"
            
            # Actually, let's use Google search to find the page
            return None  # Will use web search instead
            
    except Exception as e:
        print(f"   Error in direct search: {e}")
        return None

def extract_image_from_page_url(page_url: str) -> Optional[str]:
    """
    Extract image URL from actionfigure411.com page URL
    Pattern: /dc/multiverse/.../{slug}-{id}.php
    Image: /dc/images/{slug}-{id}.jpg
    """
    match = re.search(r'/([^/]+)-(\d+)\.php$', page_url)
    if match:
        slug = match.group(1)
        figure_id = match.group(2)
        return f"https://www.actionfigure411.com/dc/images/{slug}-{figure_id}.jpg"
    return None

def search_actionfigure411(figure_name: str) -> Optional[str]:
    """
    Search actionfigure411.com for figure page
    Returns image URL if found
    """
    try:
        # Try actionfigure411.com search
        search_query = urllib.parse.quote(figure_name)
        search_url = f"https://www.actionfigure411.com/search.php?q={search_query}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
        response = requests.get(search_url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for links to DC Multiverse pages
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if '/dc/multiverse/' in href and '.php' in href:
                    # Found a potential page
                    if not href.startswith('http'):
                        href = 'https://www.actionfigure411.com' + href
                    
                    # Extract image URL from page URL
                    img_url = extract_image_from_page_url(href)
                    if img_url:
                        # Verify the image exists
                        img_response = requests.head(img_url, headers=headers, timeout=5)
                        if img_response.status_code == 200:
                            return img_url
        
        return None
    except Exception as e:
        print(f"   Error searching actionfigure411: {e}")
        return None

def find_image_for_figure(figure: Dict) -> Optional[str]:
    """
    Try to find image URL for a figure
    Returns image URL if found
    """
    name = figure.get('name', '')
    
    if not name:
        return None
    
    # Try actionfigure411.com search
    img_url = search_actionfigure411(name)
    if img_url:
        return img_url
    
    return None

def load_progress() -> Dict:
    """Load search progress from file"""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_progress(progress: Dict):
    """Save search progress to file"""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2)

def main():
    print("=" * 60)
    print("Action Figure Image Finder")
    print("=" * 60)
    print()
    
    # Load JSON
    print(f"Loading figures from: {JSON_FILE}")
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            figures = json.load(f)
    except Exception as e:
        print(f"ERROR: Could not load JSON file: {e}")
        return
    
    print(f"   Loaded {len(figures)} total figures")
    
    # Find figures without images
    missing_images = [f for f in figures if not f.get('imageString') or f.get('imageString') == '']
    print(f"   Found {len(missing_images)} figures missing images")
    print()
    
    # Load progress
    progress = load_progress()
    searched = set(progress.get('searched', []))
    found = progress.get('found', {})
    
    print(f"   Already searched: {len(searched)} figures")
    print(f"   Already found: {len(found)} images")
    print()
    
    # Filter out already searched
    to_search = [f for f in missing_images if f.get('id') not in searched]
    
    if not to_search:
        print("All figures have been searched. Checking for new images...")
        to_search = missing_images
    
    print(f"   Figures to search: {len(to_search)}")
    print()
    print("=" * 60)
    print("Starting search...")
    print("=" * 60)
    print()
    print("NOTE: This script searches actionfigure411.com directly.")
    print("It includes delays between requests to be respectful.")
    print("If you get rate limited, wait a few minutes and run again.")
    print("Progress is saved automatically after every 10 figures.")
    print()
    
    updated_count = 0
    found_count = 0
    error_count = 0
    
    for i, figure in enumerate(to_search, 1):
        fig_id = figure.get('id')
        name = figure.get('name', 'Unknown')
        
        # Skip if already found
        if fig_id in found:
            img_url = found[str(fig_id)]
            if img_url and not figure.get('imageString'):
                figure['imageString'] = img_url
                updated_count += 1
            continue
        
        print(f"[{i}/{len(to_search)}] {name}")
        
        try:
            # Try to find image
            img_url = find_image_for_figure(figure)
            
            if img_url:
                print(f"  [FOUND] {img_url[:80]}...")
                figure['imageString'] = img_url
                found[str(fig_id)] = img_url
                found_count += 1
                updated_count += 1
            else:
                print(f"  [NOT FOUND]")
                found[str(fig_id)] = None
            
            searched.add(fig_id)
            
            # Save progress every 10 figures
            if i % 10 == 0:
                progress['searched'] = list(searched)
                progress['found'] = found
                save_progress(progress)
                print(f"  [Progress saved]")
            
            # Rate limiting
            if i < len(to_search):
                time.sleep(DELAY_BETWEEN_REQUESTS)
                
        except Exception as e:
            print(f"  [ERROR] {e}")
            error_count += 1
            searched.add(fig_id)  # Mark as searched even on error
    
    # Final save
    progress['searched'] = list(searched)
    progress['found'] = found
    save_progress(progress)
    
    # Save updated JSON
    if updated_count > 0:
        print()
        print("=" * 60)
        print("Saving results...")
        print("=" * 60)
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(figures, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults:")
        print(f"  Images found: {found_count}")
        print(f"  Figures updated: {updated_count}")
        print(f"  Errors: {error_count}")
        print(f"\nJSON file updated: {JSON_FILE}")
    else:
        print(f"\nNo new images found. {found_count} total found in this session.")
    
    print()
    print("Done!")

if __name__ == '__main__':
    main()
