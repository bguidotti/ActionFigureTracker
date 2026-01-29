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
PAGE_PUNCHERS_VISUAL_GUIDE = "https://www.actionfigure411.com/dc/page-punchers-visual-guide.php"
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
        # McFarlane only: skip Mattel (blue box 2016–2019)
        if '/mattel/' in full_path.lower():
            continue
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
            # McFarlane only: skip Mattel (blue box 2016–2019)
            if '/mattel/' in full_path.lower():
                continue
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


def scrape_page_punchers_visual_guide() -> Dict[str, Dict]:
    """
    Scrape Page Punchers visual guide. Page links directly to images: /dc/images/slug-id.jpg.
    Name from title when nearby, else from slug (e.g. the-flash-flashpoint -> The Flash Flashpoint).
    """
    log("Scraping Page Punchers visual guide...")
    html = fetch_url(PAGE_PUNCHERS_VISUAL_GUIDE)
    if not html:
        log("Failed to fetch Page Punchers visual guide")
        return {}
    figures = {}
    # Direct image links: href="/dc/images/slug-id.jpg"
    href_pattern = re.compile(r'href="(/dc/images/([a-z0-9-]+)-(\d+)\.jpg)"', re.IGNORECASE)
    title_pattern = re.compile(r'title="[^"]*Page Punchers[^"]*([^"]+)"', re.IGNORECASE)
    for m in href_pattern.finditer(html):
        full_path, slug, fig_id = m.group(1), m.group(2), m.group(3)
        image_url = f"https://www.actionfigure411.com{full_path}"
        # Try to find title within 500 chars before href (title often precedes href in HTML)
        start = max(0, m.start() - 500)
        chunk = html[start:m.end()]
        title_m = title_pattern.search(chunk)
        name = title_m.group(1).strip() if title_m else slug.replace('-', ' ').title()
        if name.lower().startswith('dc mcfarlane dc page punchers '):
            name = name[28:].strip()
        normalized = normalize_name(name)
        # Key by slug-id so we keep all figures (multiple Flash variants, etc.)
        key = f"{slug}-{fig_id}"
        if key not in figures:
            figures[key] = {
                'name': name,
                'slug': slug,
                'id': fig_id,
                'image_url': image_url,
                'page_url': PAGE_PUNCHERS_VISUAL_GUIDE,
            }
    log(f"  Found {len(figures)} Page Punchers figures")
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


def slug_from_image_url(image_url: str) -> str:
    """Extract slug from actionfigure411 image URL (e.g. .../slug-1234.jpg -> slug)."""
    if not image_url or 'actionfigure411.com' not in image_url:
        return ''
    m = re.search(r'/([a-z0-9-]+)-\d+\.(?:jpg|png|webp)', image_url, re.IGNORECASE)
    return (m.group(1) or '').lower()


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
    
    # Try matching base name to slug (require slug to start with base_slug so "flash" doesn't match "batman-flashpoint")
    base_slug = re.sub(r'[^a-z0-9\s]', '', base_name)
    base_slug = re.sub(r'\s+', '-', base_slug.strip())
    
    for key, data in scraped_figures.items():
        slug = data.get('slug', '')
        if slug == base_slug or slug.startswith(base_slug + '-'):
            return data
        # Page Punchers often use "the-flash-...", "the-joker-...", etc.
        if slug == 'the-' + base_slug or slug.startswith('the-' + base_slug + '-'):
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
    
    # Scrape Multiverse (checklist + visual guide) and Page Punchers separately
    log("\n--- Scraping Multiverse checklist ---")
    checklist_figures = scrape_checklist_for_figures()
    
    log("\n--- Scraping Multiverse visual guide ---")
    visual_guide_figures = scrape_visual_guide()
    
    # Merge Multiverse sources; McFarlane only (no Mattel)
    scraped_multiverse = {**visual_guide_figures, **checklist_figures}
    scraped_multiverse = {k: v for k, v in scraped_multiverse.items() if '/mattel/' not in (v.get('page_url') or '').lower()}
    log(f"\nTotal Multiverse figures (McFarlane only): {len(scraped_multiverse)}")
    
    log("\n--- Scraping Page Punchers visual guide ---")
    scraped_page_punchers = scrape_page_punchers_visual_guide()
    
    # Save both pools for reference
    scraped_file = os.path.join(OUTPUT_DIR, 'all_scraped_figures.json')
    with open(scraped_file, 'w', encoding='utf-8') as f:
        json.dump({"multiverse": scraped_multiverse, "page_punchers": scraped_page_punchers}, f, indent=2)
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
        base_name = re.split(r'\s*[\(\-]', name)[0].strip().lower()
        base_slug = re.sub(r'[^a-z0-9\s]', '', base_name)
        base_slug = re.sub(r'\s+', '-', base_slug.strip())
        current_slug = slug_from_image_url(current_image)
        # Consider current image "wrong" if it's actionfigure411 but slug doesn't match our character (e.g. batman-flashpoint for a Flash figure)
        current_is_wrong = (
            current_slug
            and (not base_slug or not (current_slug == base_slug or current_slug.startswith(base_slug + '-')))
        )
        
        # Skip only if already using actionfigure411 and current image slug matches our base (correct)
        if 'actionfigure411.com' in current_image and not current_is_wrong:
            already_411 += 1
            continue
        
        # Use the correct pool: Page Punchers figures only match Page Punchers images; Multiverse only Multiverse
        scraped_pool = scraped_page_punchers if figure.get('series') == 'dc-page-punchers' else scraped_multiverse
        match = find_best_match(name, scraped_pool)
        
        if match:
            image_url = match['image_url']
            
            # Verify the image exists
            if check_image_exists(image_url):
                old_source = "wrong_match" if current_is_wrong else ("legendsverse" if "legendsverse" in current_image else ("none" if not current_image else "other"))
                figure['imageString'] = image_url
                updated += 1
                if updated <= 50 or updated % 100 == 0 or current_is_wrong:  # Show first 50, every 100th, and every wrong-match fix
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
