#!/usr/bin/env python3
"""
Update figure images based on actionfigure411.com URL patterns
Constructs image URLs from page URLs found via web search
"""

import json
import re

def construct_actionfigure411_image_url(page_url: str) -> str:
    """
    Construct image URL from actionfigure411.com page URL
    Pattern: /dc/multiverse/.../{slug}-{id}.php
    Image: /dc/images/{slug}-{id}.jpg
    """
    # Extract slug and ID from URL
    match = re.search(r'/([^/]+)-(\d+)\.php$', page_url)
    if match:
        slug = match.group(1)
        figure_id = match.group(2)
        return f"https://www.actionfigure411.com/dc/images/{slug}-{figure_id}.jpg"
    return None

# Known mappings from web search results
# Format: (figure_name_pattern, page_url)
KNOWN_IMAGES = [
    ("Azrael (White Knight)", "https://www.actionfigure411.com/dc/multiverse/mcfarlane/azrael-curse-of-the-white-knight-1-2942.php"),
    ("Cyborg (Teen Titans Animated)", "https://www.actionfigure411.com/dc/multiverse/mcfarlane/cyborg-teen-titans-2948.php"),
    ("Batman Who Laughs (Sky Tyrant Wings)", "https://www.actionfigure411.com/dc/multiverse/the-merciless-baf/batman-who-laughs-2957.php"),
]

def normalize_name(name: str) -> str:
    """Normalize figure name for matching"""
    name = re.sub(r'\s+', ' ', name.strip())
    name = name.replace(':', ' ').replace('(', ' ').replace(')', ' ')
    name = re.sub(r'\s+', ' ', name)
    return name.lower().strip()

def find_matching_figure(figures, search_name):
    """Find figure by normalized name"""
    normalized_search = normalize_name(search_name)
    for fig in figures:
        fig_name = normalize_name(fig.get('name', ''))
        if fig_name == normalized_search:
            return fig
        # Try partial match
        if normalized_search in fig_name or fig_name in normalized_search:
            return fig
    return None

def main():
    json_file = r'c:\Code\ActionFigureTracker\Models\all_figures.json'
    
    with open(json_file, 'r', encoding='utf-8') as f:
        figures = json.load(f)
    
    updated = 0
    
    print("Updating images from known URLs...\n")
    
    for search_name, page_url in KNOWN_IMAGES:
        fig = find_matching_figure(figures, search_name)
        if fig:
            img_url = construct_actionfigure411_image_url(page_url)
            if img_url and not fig.get('imageString'):
                fig['imageString'] = img_url
                print(f"[OK] {fig['name']}")
                print(f"  {img_url}")
                updated += 1
            elif fig.get('imageString'):
                print(f"[-] {fig['name']} (already has image)")
            else:
                print(f"[X] {fig['name']} (could not construct URL)")
        else:
            print(f"[?] {search_name} (not found in JSON)")
    
    if updated > 0:
        print(f"\n\nUpdated {updated} figures. Saving JSON...")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(figures, f, indent=2, ensure_ascii=False)
        print("Done!")
    else:
        print("\nNo updates made.")

if __name__ == '__main__':
    main()
