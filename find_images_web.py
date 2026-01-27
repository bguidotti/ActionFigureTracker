#!/usr/bin/env python3
"""
Find image URLs for figures using web search
Processes figures in batches
"""

import json
import re
from typing import Optional, List, Dict

def extract_image_url_from_search_results(search_text: str, figure_name: str) -> Optional[str]:
    """
    Extract image URL from web search results text
    Looks for actionfigure411.com and legendsverse.com image URLs
    """
    # Pattern for actionfigure411.com images
    actionfigure_patterns = [
        r'https://www\.actionfigure411\.com/dc/images/[^"\s<>]+\.(jpg|png|webp)',
        r'actionfigure411\.com/dc/images/[^"\s<>]+\.(jpg|png|webp)',
    ]
    
    # Pattern for legendsverse.com images  
    legendsverse_patterns = [
        r'https://media\.legendsverse\.com/[^"\s<>]+(?:card|description)[^"\s<>]*\.(jpg|png|webp)',
        r'media\.legendsverse\.com/[^"\s<>]+(?:card|description)[^"\s<>]*\.(jpg|png|webp)',
    ]
    
    # Try legendsverse first (better quality, matches existing images)
    for pattern in legendsverse_patterns:
        matches = re.findall(pattern, search_text, re.IGNORECASE)
        if matches:
            url = matches[0] if isinstance(matches[0], str) else matches[0]
            if not url.startswith('http'):
                url = 'https://' + url
            return url
    
    # Try actionfigure411
    for pattern in actionfigure_patterns:
        matches = re.findall(pattern, search_text, re.IGNORECASE)
        if matches:
            url = matches[0] if isinstance(matches[0], str) else matches[0]
            if not url.startswith('http'):
                url = 'https://' + url
            # Prefer full size over thumbnails
            if 'thumbs' in url:
                url = url.replace('/thumbs/', '/')
            return url
    
    return None

def main():
    json_file = r'c:\Code\ActionFigureTracker\Models\all_figures.json'
    
    with open(json_file, 'r', encoding='utf-8') as f:
        figures = json.load(f)
    
    # Find figures without images
    missing_images = [f for f in figures if not f.get('imageString') or f.get('imageString') == '']
    
    print(f"Found {len(missing_images)} figures missing images")
    print(f"\nI'll need to search the web for each figure.")
    print(f"This will require multiple web searches.")
    print(f"\nLet me create a list of search queries for the first 10 figures:\n")
    
    for i, figure in enumerate(missing_images[:10], 1):
        name = figure.get('name', '')
        series = figure.get('series', 'dc-multiverse')
        search_query = f"{name} {series} mcfarlane action figure site:actionfigure411.com OR site:legendsverse.com"
        print(f"{i}. {name}")
        print(f"   Search: {search_query}")
        print()

if __name__ == '__main__':
    main()
