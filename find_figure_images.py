#!/usr/bin/env python3
"""
Find image URLs for figures missing images
Searches actionfigure411.com and other sources
"""

import json
import re
import time
from typing import Optional, List, Dict
import urllib.parse

def clean_figure_name(name: str) -> str:
    """Clean figure name for search"""
    # Remove common suffixes
    name = re.sub(r'\s*\(.*?\)', '', name)  # Remove parentheticals
    name = name.strip()
    return name

def search_actionfigure411(figure_name: str, series: str = "DC Multiverse") -> Optional[str]:
    """
    Search actionfigure411.com for figure image
    Returns image URL if found
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        
        # Clean the name for URL
        search_name = urllib.parse.quote_plus(figure_name)
        search_url = f"https://www.actionfigure411.com/search?q={search_name}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for image tags - adjust selectors based on site structure
            # Try common image patterns
            img_tags = soup.find_all('img', src=True)
            for img in img_tags:
                src = img.get('src', '')
                if 'card' in src.lower() or 'figure' in src.lower() or 'product' in src.lower():
                    if src.startswith('http'):
                        return src
                    elif src.startswith('//'):
                        return 'https:' + src
                    elif src.startswith('/'):
                        return 'https://www.actionfigure411.com' + src
        
        return None
    except Exception as e:
        print(f"   Error searching actionfigure411: {e}")
        return None

def search_legendsverse(figure_name: str) -> Optional[str]:
    """
    Search legendsverse.com (the source of existing images)
    Returns image URL if found
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        
        search_name = urllib.parse.quote_plus(figure_name)
        search_url = f"https://www.legendsverse.com/search?q={search_name}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for media.legendsverse.com image URLs
            img_tags = soup.find_all('img', src=True)
            for img in img_tags:
                src = img.get('src', '')
                if 'media.legendsverse.com' in src and ('card' in src.lower() or 'description' in src.lower()):
                    if src.startswith('http'):
                        return src
                    elif src.startswith('//'):
                        return 'https:' + src
        
        return None
    except Exception as e:
        print(f"   Error searching legendsverse: {e}")
        return None

def search_google_images(figure_name: str, series: str = "DC Multiverse") -> Optional[str]:
    """
    Search Google Images for figure
    Returns first relevant image URL
    """
    try:
        # Use web search to find images
        # Note: This is a simplified approach - in production you'd use Google Custom Search API
        search_query = f"{figure_name} {series} action figure mcfarlane"
        # For now, return None - we'll use web_search tool instead
        return None
    except Exception as e:
        print(f"   Error searching Google: {e}")
        return None

def find_image_for_figure(figure: Dict, use_web_search: bool = False) -> Optional[str]:
    """
    Try to find image URL for a figure
    Returns image URL if found
    """
    name = figure.get('name', '')
    series = figure.get('series', 'dc-multiverse')
    
    print(f"  Searching for: {name}")
    
    # Try legendsverse first (source of existing images)
    img_url = search_legendsverse(name)
    if img_url:
        print(f"    Found on legendsverse: {img_url[:80]}...")
        return img_url
    
    # Try actionfigure411
    img_url = search_actionfigure411(name, series)
    if img_url:
        print(f"    Found on actionfigure411: {img_url[:80]}...")
        return img_url
    
    print(f"    No image found")
    return None

def main():
    # Load JSON
    json_file = r'c:\Code\ActionFigureTracker\Models\all_figures.json'
    
    with open(json_file, 'r', encoding='utf-8') as f:
        figures = json.load(f)
    
    # Find figures without images
    missing_images = [f for f in figures if not f.get('imageString') or f.get('imageString') == '']
    
    print(f"Found {len(missing_images)} figures missing images")
    print(f"Starting search...\n")
    
    updated_count = 0
    found_count = 0
    
    # Process first 10 as a test
    for i, figure in enumerate(missing_images[:10], 1):
        print(f"\n[{i}/{min(10, len(missing_images))}] {figure.get('name')}")
        img_url = find_image_for_figure(figure)
        
        if img_url:
            figure['imageString'] = img_url
            found_count += 1
            updated_count += 1
        else:
            updated_count += 1  # Mark as searched even if not found
        
        # Be respectful - add delay between requests
        time.sleep(2)
    
    # Save updated JSON
    if found_count > 0:
        print(f"\n\nFound {found_count} images out of {updated_count} searched")
        print("Saving updated JSON...")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(figures, f, indent=2, ensure_ascii=False)
        print("Done!")
    else:
        print("\n\nNo images found. You may need to install requests and beautifulsoup4:")
        print("  pip install requests beautifulsoup4")

if __name__ == '__main__':
    main()
