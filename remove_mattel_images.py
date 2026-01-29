#!/usr/bin/env python3
"""
Remove blue box Mattel DC Multiverse images from the figure database and scraped image data.

- Collects image URLs that come from Mattel (page_url contains /mattel/) in scraped JSONs
- Clears imageString in all_figures.json for any figure using those URLs
- Removes Mattel entries from downloaded_images/all_scraped_figures.json and scraped_figures.json
  so future image matching won't use blue box Mattel pictures (McFarlane only).
"""

import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(SCRIPT_DIR, 'Models', 'all_figures.json')
DOWNLOADED = os.path.join(SCRIPT_DIR, 'downloaded_images')
ALL_SCRAPED = os.path.join(DOWNLOADED, 'all_scraped_figures.json')
SCRAPED = os.path.join(DOWNLOADED, 'scraped_figures.json')


def _iter_scraped_entries(data):
    """Yield (key, entry) from scraped data; supports flat dict or {multiverse, page_punchers} format."""
    if isinstance(data, dict) and ('multiverse' in data or 'page_punchers' in data):
        for pool in (data.get('multiverse', {}), data.get('page_punchers', {})):
            for k, v in pool.items():
                yield k, v
    else:
        for k, v in (data or {}).items():
            yield k, v


def get_mattel_image_urls(scraped_path: str) -> set:
    """Collect image_url values where page_url contains /mattel/"""
    urls = set()
    if not os.path.exists(scraped_path):
        return urls
    with open(scraped_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for key, entry in _iter_scraped_entries(data):
        if isinstance(entry, dict) and '/mattel/' in entry.get('page_url', ''):
            url = entry.get('image_url', '')
            if url:
                urls.add(url)
    return urls


def main():
    mattel_urls = set()
    for path in (ALL_SCRAPED, SCRAPED):
        mattel_urls |= get_mattel_image_urls(path)
    print(f"Found {len(mattel_urls)} Mattel (blue box) image URLs in scraped data")
    for u in sorted(mattel_urls):
        print(f"  - {u}")

    # Clear those imageStrings in all_figures.json
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        figures = json.load(f)
    cleared = 0
    for fig in figures:
        img = fig.get('imageString', '') or ''
        if img in mattel_urls:
            fig['imageString'] = ''
            cleared += 1
            print(f"  Cleared image for: {fig.get('name', '?')}")
    print(f"\nCleared imageString for {cleared} figures in {JSON_FILE}")
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(figures, f, indent=2)

    # Remove Mattel entries from scraped JSONs (support flat or {multiverse, page_punchers} format)
    for scraped_path in (ALL_SCRAPED, SCRAPED):
        if not os.path.exists(scraped_path):
            continue
        with open(scraped_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict) and ('multiverse' in data or 'page_punchers' in data):
            before = len(data.get('multiverse', {}))
            data['multiverse'] = {k: v for k, v in (data.get('multiverse') or {}).items()
                                  if '/mattel/' not in (v.get('page_url') or '')}
            removed = before - len(data.get('multiverse', {}))
        else:
            before = len(data)
            data = {k: v for k, v in data.items() if '/mattel/' not in (v.get('page_url') or '')}
            removed = before - len(data)
        if removed:
            with open(scraped_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print(f"Removed {removed} Mattel entries from {os.path.basename(scraped_path)}")
    print("Done.")


if __name__ == '__main__':
    main()
