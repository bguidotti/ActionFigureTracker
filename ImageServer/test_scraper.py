"""Test scraper to find working approach"""
import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
import json

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}


def test_legendsverse(query):
    """Test LegendsVerse scraping"""
    print(f"\n=== Testing LegendsVerse for '{query}' ===")
    url = f'https://legendsverse.com/?s={urllib.parse.quote(query)}'
    resp = requests.get(url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    results = []
    
    # Find figure links
    figure_links = soup.find_all('a', href=re.compile(r'/figures/'))
    print(f"Found {len(figure_links)} figure links")
    
    seen = set()
    for a in figure_links[:50]:
        href = a.get('href')
        if href in seen:
            continue
        seen.add(href)
        
        img = a.find('img')
        if img:
            src = img.get('src') or img.get('data-src')
            if src and 'media.legendsverse.com' in src:
                title = a.get_text(strip=True) or img.get('alt', '') or 'Unknown'
                title = re.sub(r'\s+', ' ', title).strip()[:80]
                if title and len(title) > 3:
                    # Get higher res image
                    full_src = src.replace('-card.jpg', '.jpg').replace('-thumb.jpg', '.jpg')
                    results.append({'title': title, 'url': full_src, 'source': 'LegendsVerse'})
    
    print(f"Extracted {len(results)} unique figures")
    for r in results[:5]:
        print(f"  - {r['title'][:50]}")
        print(f"    {r['url'][:70]}")
    
    return results


def test_mcfarlane(query):
    """Test McFarlane.com scraping"""
    print(f"\n=== Testing McFarlane for '{query}' ===")
    url = f'https://mcfarlane.com/search/?q={urllib.parse.quote(query)}'
    resp = requests.get(url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    results = []
    
    # Find product cards
    products = soup.find_all(['div', 'article'], class_=re.compile(r'product|item|card'))
    print(f"Found {len(products)} product containers")
    
    # Also look for img tags directly
    imgs = soup.find_all('img')
    mcf_imgs = [img for img in imgs if img.get('src') and 'mcfarlane' in img.get('src', '').lower()]
    print(f"Found {len(mcf_imgs)} mcfarlane images")
    
    for img in mcf_imgs[:20]:
        src = img.get('src')
        alt = img.get('alt', 'Unknown')
        if src and len(alt) > 3:
            # Make absolute
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                src = 'https://mcfarlane.com' + src
            results.append({'title': alt, 'url': src, 'source': 'McFarlane'})
    
    print(f"Extracted {len(results)} figures")
    for r in results[:5]:
        print(f"  - {r['title'][:50]}")
        print(f"    {r['url'][:70]}")
    
    return results


def test_actionfigure411_direct():
    """Try direct figure page on AF411"""
    print(f"\n=== Testing ActionFigure411 Direct Page ===")
    # Try a specific figure page
    url = 'https://www.actionfigure411.com/dc/dc-multiverse/batman-4950.htm'
    resp = requests.get(url, headers=HEADERS, timeout=15)
    print(f"Status: {resp.status_code}, Length: {len(resp.text)}")
    
    soup = BeautifulSoup(resp.text, 'html.parser')
    imgs = soup.find_all('img')
    print(f"Found {len(imgs)} images on page")
    
    for img in imgs:
        src = img.get('src', '')
        if 'actionfigure411.com/dc/images' in src:
            print(f"  Found figure image: {src}")


if __name__ == '__main__':
    test_legendsverse('Batman DC Multiverse')
    test_mcfarlane('Batman')
    test_actionfigure411_direct()
