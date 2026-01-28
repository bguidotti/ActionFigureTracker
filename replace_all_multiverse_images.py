#!/usr/bin/env python3
"""
Replace ALL DC Multiverse images with larger ones from actionfigure411.com

This script:
1. Scrapes the visual guide to get all figure image URLs
2. Matches ALL DC Multiverse figures (not just missing ones)
3. Replaces existing images with actionfigure411.com URLs
"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

def log(msg: str):
    """Print with immediate flush"""
    print(msg)
    sys.stdout.flush()

# Config
JSON_FILE = r'c:\Code\ActionFigureTracker\Models\all_figures.json'
OUTPUT_DIR = r'c:\Code\ActionFigureTracker\downloaded_images'
VISUAL_GUIDE_BASE = "https://www.actionfigure411.com/dc/multiverse-visual-guide.php"
CHECKLIST_URL = "https://www.actionfigure411.com/dc/multiverse-checklist.php"
BASE_IMAGE_URL = "https://www.actionfigure411.com/dc/images"
DELAY_BETWEEN_REQUESTS = 0.3  # seconds

# User agent to avoid being blocked
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
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


def check_image_exists(url: str) -> bool:
    """Check if an image URL exists (HEAD request)"""
    try:
        req = urllib.request.Request(url, headers=HEADERS, method='HEAD')
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status == 200
    except:
        return False


def scrape_checklist_for_figures() -> Dict[str, Dict]:
    """
    Scrape the checklist page to get figure URLs and then fetch each to get image
    Returns dict of {normalized_name: {name, image_url, page_url}}
    """
    log("Scraping checklist to get all figure links...")
    
    html = fetch_url(CHECKLIST_URL)
    if not html:
        log("Failed to fetch checklist")
        return {}
    
    # Find all figure links
    # Pattern: <a href="...multiverse/.../name-id.php">Figure Name</a>
    link_pattern = r'<a[^>]+href="(/dc/multiverse/[^"]+/([a-z0-9-]+)-(\d+)\.php)"[^>]*>([^<]+)</a>'
    matches = re.findall(link_pattern, html, re.IGNORECASE)
    
    log(f"Found {len(matches)} figure links in checklist")
    
    figures = {}
    for full_path, slug, fig_id, name in matches:
        # Clean up name
        name = name.strip()
        name = re.sub(r'&amp;', '&', name)
        name = re.sub(r'&#\d+;', '', name)
        
        # Construct image URL (standard pattern for actionfigure411)
        image_url = f"{BASE_IMAGE_URL}/{slug}-{fig_id}.jpg"
        
        normalized = normalize_name(name)
        figures[normalized] = {
            'name': name,
            'slug': slug,
            'id': fig_id,
            'image_url': image_url,
            'page_url': f"https://www.actionfigure411.com{full_path}"
        }
    
    return figures


def scrape_visual_guide() -> Dict[str, Dict]:
    """
    Scrape all visual guide pages to get figure name -> image URL mappings
    Returns dict of {normalized_name: {name, image_url, page_url, slug, id}}
    """
    log("Scraping visual guide pages...")
    figures = {}
    
    page_num = 1
    max_pages = 30  # Safety limit
    
    while page_num <= max_pages:
        if page_num == 1:
            url = VISUAL_GUIDE_BASE
        else:
            url = f"{VISUAL_GUIDE_BASE}?page={page_num}"
        
        log(f"  Fetching page {page_num}...")
        html = fetch_url(url)
        
        if not html:
            log(f"  Failed to fetch page {page_num}, stopping")
            break
        
        # Find all figure entries with images
        # Pattern: looking for image src and associated link
        # <a href="/dc/multiverse/.../slug-id.php">...<img src="..."></a>
        
        # First find all figure container blocks
        figure_pattern = r'<a[^>]+href="(/dc/multiverse/[^"]+/([a-z0-9-]+)-(\d+)\.php)"[^>]*>.*?</a>'
        
        # Also try to find direct link patterns
        link_pattern = r'href="(/dc/multiverse/[^"]+/([a-z0-9-]+)-(\d+)\.php)"'
        matches = re.findall(link_pattern, html, re.IGNORECASE)
        
        if not matches:
            log(f"  No figures found on page {page_num}, stopping")
            break
        
        page_figures = 0
        for full_path, slug, fig_id in matches:
            # Construct name from slug
            name = slug.replace('-', ' ').title()
            
            # Image URL follows pattern: /dc/images/slug-id.jpg
            image_url = f"{BASE_IMAGE_URL}/{slug}-{fig_id}.jpg"
            
            normalized = normalize_name(name)
            if normalized not in figures:
                figures[normalized] = {
                    'name': name,
                    'slug': slug,
                    'id': fig_id,
                    'image_url': image_url,
                    'page_url': f"https://www.actionfigure411.com{full_path}"
                }
                page_figures += 1
        
        log(f"  Found {page_figures} new figures on page {page_num}")
        
        # Check if there's a next page
        if f'page={page_num + 1}' not in html:
            log(f"  No more pages after {page_num}")
            break
        
        page_num += 1
        time.sleep(DELAY_BETWEEN_REQUESTS)
    
    log(f"\nTotal unique figures found: {len(figures)}")
    return figures


def normalize_name(name: str) -> str:
    """Normalize a figure name for matching"""
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
    
    # Extract the base character name (before first parenthesis)
    base_name = re.split(r'\s*[\(\-]', figure_name)[0].strip().lower()
    
    # Try matching by slug
    slug_from_name = figure_name.lower()
    slug_from_name = re.sub(r'\([^)]*\)', '', slug_from_name)
    slug_from_name = re.sub(r'[^a-z0-9\s]', '', slug_from_name)
    slug_from_name = re.sub(r'\s+', '-', slug_from_name.strip())
    
    for key, data in scraped_figures.items():
        if data['slug'] == slug_from_name:
            return data
    
    # Try matching base name to slug
    base_slug = re.sub(r'[^a-z0-9\s]', '', base_name)
    base_slug = re.sub(r'\s+', '-', base_slug.strip())
    
    for key, data in scraped_figures.items():
        if data['slug'].startswith(base_slug) or base_slug in data['slug']:
            return data
    
    # Try fuzzy matching with lower threshold
    best_match = None
    best_score = 0.0
    
    for key, data in scraped_figures.items():
        # Match on full name
        score = fuzzy_match(figure_name, data['name'])
        if score > best_score and score > 0.65:
            best_score = score
            best_match = data
        
        # Also try matching just base names
        their_base = re.split(r'\s*[\(\-]', data['name'])[0].strip()
        base_score = fuzzy_match(base_name, their_base.lower())
        if base_score > 0.85 and base_score > best_score:
            best_score = base_score
            best_match = data
    
    # Try word overlap matching - more flexible
    for key, data in scraped_figures.items():
        our_parts = set(normalize_name(figure_name).split())
        their_parts = set(normalize_name(data['name']).split())
        
        # Remove common filler words
        filler = {'the', 'a', 'an', 'of', 'and', 'version', 'variant', 'edition'}
        our_parts = our_parts - filler
        their_parts = their_parts - filler
        
        common = our_parts & their_parts
        if len(common) >= 2:
            # Weight by how much of our name is matched
            overlap = len(common) / len(our_parts) if our_parts else 0
            if overlap > 0.5 and overlap > best_score:
                best_score = overlap
                best_match = data
    
    # Special handling for character variants - try to find any match for the character
    if not best_match and base_name:
        # Look for any figure with the same base character name
        for key, data in scraped_figures.items():
            their_base = re.split(r'\s*[\(\-]', data['name'])[0].strip().lower()
            if base_name == their_base:
                return data  # Return first match for this character
    
    return best_match


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Load our figures
    log(f"Loading figures from {JSON_FILE}...")
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        all_figures = json.load(f)
    
    # Get ALL DC Multiverse and Page Punchers figures (not just missing)
    multiverse_figures = [f for f in all_figures if f.get('series') in ['dc-multiverse', 'dc-page-punchers']]
    log(f"Found {len(multiverse_figures)} DC Multiverse/Page Punchers figures total")
    
    # Scrape both checklist and visual guide for maximum coverage
    log("\n--- Scraping checklist ---")
    checklist_figures = scrape_checklist_for_figures()
    
    log("\n--- Scraping visual guide ---")
    visual_guide_figures = scrape_visual_guide()
    
    # Merge both sources (checklist has better name matching, visual guide has more entries)
    scraped = {**visual_guide_figures, **checklist_figures}  # checklist overwrites
    log(f"\nTotal scraped figures from both sources: {len(scraped)}")
    
    # Save scraped data for reference
    scraped_file = os.path.join(OUTPUT_DIR, 'all_scraped_figures.json')
    with open(scraped_file, 'w', encoding='utf-8') as f:
        json.dump(scraped, f, indent=2)
    log(f"Saved scraped data to {scraped_file}")
    
    # Match and update ALL figures
    log("\n" + "="*60)
    log("Matching figures and updating image URLs...")
    log("="*60)
    
    updated = 0
    already_411 = 0
    failed = []
    
    for i, figure in enumerate(multiverse_figures):
        name = figure['name']
        current_image = figure.get('imageString', '')
        
        # Check if already using actionfigure411
        if 'actionfigure411.com' in current_image:
            already_411 += 1
            continue
        
        # Try to find a match
        match = find_best_match(name, scraped)
        
        if match:
            image_url = match['image_url']
            
            # Verify the image exists
            if check_image_exists(image_url):
                old_source = "legendsverse" if "legendsverse" in current_image else ("none" if not current_image else "other")
                figure['imageString'] = image_url
                updated += 1
                if updated <= 50 or updated % 100 == 0:  # Show first 50 and then every 100th
                    log(f"[{updated}] {name}")
                    log(f"    {old_source} -> actionfigure411")
            else:
                failed.append({'name': name, 'reason': 'Image not accessible', 'tried_url': image_url})
        else:
            failed.append({'name': name, 'reason': 'No match found', 'current': current_image})
        
        # Progress update
        if (i + 1) % 50 == 0:
            log(f"  Progress: {i+1}/{len(multiverse_figures)} processed, {updated} updated...")
            time.sleep(0.2)
    
    # Save updated JSON
    log(f"\n\nSaving updated data to {JSON_FILE}...")
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_figures, f, indent=2)
    
    # Summary
    log("\n" + "="*60)
    log("SUMMARY")
    log("="*60)
    log(f"Total DC figures: {len(multiverse_figures)}")
    log(f"Already using actionfigure411: {already_411}")
    log(f"Updated to actionfigure411: {updated}")
    log(f"Failed to update: {len(failed)}")
    
    if failed:
        failed_file = os.path.join(OUTPUT_DIR, 'failed_image_updates.json')
        with open(failed_file, 'w', encoding='utf-8') as f:
            json.dump(failed, f, indent=2)
        log(f"\nFailed matches saved to {failed_file}")
        
        log("\nSample failed figures:")
        for f in failed[:15]:
            log(f"  - {f['name']}: {f['reason']}")
        if len(failed) > 15:
            log(f"  ... and {len(failed) - 15} more")


if __name__ == '__main__':
    main()
