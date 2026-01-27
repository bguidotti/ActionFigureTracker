#!/usr/bin/env python3
"""
Download DC Multiverse images from actionfigure411.com

Strategy:
1. Scrape the visual guide pages to get all figure URLs with their IDs
2. Match figures by name to our JSON data
3. Download images for figures missing them
"""

import json
import os
import re
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher

# Config
JSON_FILE = r'c:\Code\ActionFigureTracker\Models\all_figures.json'
IMAGES_DIR = r'c:\Code\ActionFigureTracker\downloaded_images'
VISUAL_GUIDE_URL = "https://www.actionfigure411.com/dc/multiverse-visual-guide.php"
BASE_IMAGE_URL = "https://www.actionfigure411.com/dc/images"
DELAY_BETWEEN_REQUESTS = 0.5  # seconds

# User agent to avoid being blocked
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}


def fetch_url(url: str) -> Optional[str]:
    """Fetch a URL and return its content as string"""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return None


def download_image(url: str, save_path: str) -> bool:
    """Download an image from URL to local path"""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as response:
            with open(save_path, 'wb') as f:
                f.write(response.read())
        return True
    except Exception as e:
        print(f"  Error downloading {url}: {e}")
        return False


def check_image_exists(url: str) -> bool:
    """Check if an image URL exists (HEAD request)"""
    try:
        req = urllib.request.Request(url, headers=HEADERS, method='HEAD')
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status == 200
    except:
        return False


def scrape_visual_guide() -> Dict[str, str]:
    """
    Scrape the visual guide to get figure name -> image URL mappings
    Returns dict of {figure_name: image_url}
    """
    print("Scraping visual guide pages...")
    figures = {}
    
    # The visual guide has multiple pages - try to get them all
    page_num = 1
    max_pages = 20  # Safety limit
    
    while page_num <= max_pages:
        if page_num == 1:
            url = VISUAL_GUIDE_URL
        else:
            url = f"https://www.actionfigure411.com/dc/multiverse-visual-guide.php?page={page_num}"
        
        print(f"  Fetching page {page_num}: {url}")
        html = fetch_url(url)
        
        if not html:
            print(f"  Failed to fetch page {page_num}, stopping")
            break
        
        # Find figure links and extract info
        # Pattern: href="/dc/multiverse/mcfarlane/SLUG-ID.php"
        # or href="/dc/multiverse/SUBFOLDER/SLUG-ID.php"
        link_pattern = r'href="(/dc/multiverse/[^"]+/([a-z0-9-]+)-(\d+)\.php)"'
        matches = re.findall(link_pattern, html, re.IGNORECASE)
        
        if not matches:
            print(f"  No figures found on page {page_num}, stopping")
            break
        
        for full_path, slug, fig_id in matches:
            # Extract figure name from slug
            name = slug.replace('-', ' ').title()
            image_url = f"{BASE_IMAGE_URL}/{slug}-{fig_id}.jpg"
            figures[name.lower()] = {
                'name': name,
                'slug': slug,
                'id': fig_id,
                'image_url': image_url,
                'page_url': f"https://www.actionfigure411.com{full_path}"
            }
        
        print(f"  Found {len(matches)} figures on page {page_num}")
        
        # Check if there's a next page
        if f'page={page_num + 1}' not in html and 'Next' not in html:
            print(f"  No more pages after {page_num}")
            break
        
        page_num += 1
        time.sleep(DELAY_BETWEEN_REQUESTS)
    
    print(f"\nTotal figures found on actionfigure411: {len(figures)}")
    return figures


def normalize_name(name: str) -> str:
    """Normalize a figure name for matching - keep parenthetical content"""
    name = name.lower()
    # Remove # symbols but keep the numbers
    name = re.sub(r'#', '', name)
    # Replace parentheses with spaces but keep their content
    name = re.sub(r'[()]', ' ', name)
    # Replace hyphens with spaces
    name = re.sub(r'\s*-\s*', ' ', name)
    # Remove other punctuation
    name = re.sub(r'[^\w\s]', '', name)
    # Collapse whitespace
    name = re.sub(r'\s+', ' ', name)
    return name.strip()


def fuzzy_match(name1: str, name2: str) -> float:
    """Return similarity ratio between two names"""
    return SequenceMatcher(None, normalize_name(name1), normalize_name(name2)).ratio()


def find_best_match(figure_name: str, scraped_figures: Dict) -> Optional[Dict]:
    """Find the best matching figure from scraped data"""
    normalized = normalize_name(figure_name)
    
    # Try exact match first (on normalized key)
    if normalized in scraped_figures:
        return scraped_figures[normalized]
    
    # Also try matching the full original name to the slug
    slug_from_name = figure_name.lower()
    slug_from_name = re.sub(r'\([^)]*\)', '', slug_from_name)
    slug_from_name = re.sub(r'[^a-z0-9\s]', '', slug_from_name)
    slug_from_name = re.sub(r'\s+', '-', slug_from_name.strip())
    
    for key, data in scraped_figures.items():
        if data['slug'] == slug_from_name:
            return data
    
    # Try fuzzy matching - need higher threshold (85%) for accuracy
    best_match = None
    best_score = 0.0
    
    for key, data in scraped_figures.items():
        score = fuzzy_match(figure_name, data['name'])
        if score > best_score and score > 0.85:  # 85% threshold for better accuracy
            best_score = score
            best_match = data
    
    # Also try matching with parenthetical content included
    for key, data in scraped_figures.items():
        # Check if the scraped name contains key parts of our figure name
        our_parts = set(normalize_name(figure_name).split())
        their_parts = set(normalize_name(data['name']).split())
        
        # Both names should share significant words
        common = our_parts & their_parts
        if len(common) >= 2:  # At least 2 words in common
            # Calculate overlap
            overlap = len(common) / max(len(our_parts), len(their_parts))
            if overlap > 0.6 and overlap > best_score:
                best_score = overlap
                best_match = data
    
    return best_match


def construct_image_url_from_name(name: str) -> str:
    """
    Try to construct an image URL directly from the figure name
    This is a fallback when scraping doesn't find the figure
    """
    slug = name.lower()
    slug = re.sub(r'\([^)]*\)', '', slug)  # Remove parentheses
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)  # Keep only alphanumeric and spaces
    slug = re.sub(r'\s+', '-', slug.strip())  # Replace spaces with hyphens
    slug = re.sub(r'-+', '-', slug)  # Collapse multiple hyphens
    slug = slug.strip('-')
    
    # We don't know the ID, so return None
    # This function is mainly useful for pattern recognition
    return slug


def main():
    # Create images directory
    os.makedirs(IMAGES_DIR, exist_ok=True)
    
    # Load our figures
    print(f"Loading figures from {JSON_FILE}...")
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        all_figures = json.load(f)
    
    # Filter to DC Multiverse figures missing images
    missing = [f for f in all_figures 
               if f.get('series') == 'dc-multiverse' 
               and (not f.get('imageString') or f.get('imageString') == '')]
    
    print(f"Found {len(missing)} DC Multiverse figures missing images")
    
    if not missing:
        print("No figures missing images!")
        return
    
    # Scrape the visual guide
    scraped = scrape_visual_guide()
    
    if not scraped:
        print("Failed to scrape any figures from the visual guide")
        print("Let me try an alternative approach...")
        # Try fetching individual figure pages based on name patterns
    
    # Save scraped data for reference
    scraped_file = os.path.join(IMAGES_DIR, 'scraped_figures.json')
    with open(scraped_file, 'w', encoding='utf-8') as f:
        json.dump(scraped, f, indent=2)
    print(f"Saved scraped data to {scraped_file}")
    
    # Match and download
    print("\nMatching figures and downloading images...")
    updated = 0
    failed = []
    
    for i, figure in enumerate(missing):
        name = figure['name']
        print(f"\n[{i+1}/{len(missing)}] {name}")
        
        # Try to find a match
        match = find_best_match(name, scraped)
        
        if match:
            image_url = match['image_url']
            print(f"  Found match: {match['name']}")
            print(f"  Image URL: {image_url}")
            
            # Verify the image exists
            if check_image_exists(image_url):
                # Update the figure in our data
                figure['imageString'] = image_url
                updated += 1
                print(f"  [OK] Image verified and URL updated")
            else:
                print(f"  [FAIL] Image URL not accessible")
                failed.append({'name': name, 'reason': 'Image not accessible', 'tried_url': image_url})
        else:
            print(f"  [SKIP] No match found in scraped data")
            failed.append({'name': name, 'reason': 'No match found'})
        
        time.sleep(DELAY_BETWEEN_REQUESTS)
    
    # Save updated JSON
    print(f"\nUpdating {JSON_FILE}...")
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_figures, f, indent=2)
    
    # Summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"Total missing images: {len(missing)}")
    print(f"Successfully updated: {updated}")
    print(f"Failed: {len(failed)}")
    
    if failed:
        failed_file = os.path.join(IMAGES_DIR, 'failed_matches.json')
        with open(failed_file, 'w', encoding='utf-8') as f:
            json.dump(failed, f, indent=2)
        print(f"\nFailed matches saved to {failed_file}")
        print("\nFailed figures:")
        for f in failed[:20]:  # Show first 20
            print(f"  - {f['name']}: {f['reason']}")
        if len(failed) > 20:
            print(f"  ... and {len(failed) - 20} more")


if __name__ == '__main__':
    main()
