"""
Action Figure Image Search API
A Flask backend that scrapes action figure sites for images
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from difflib import SequenceMatcher
import time
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Allow iOS app to connect

# User agent to avoid being blocked
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Cache for visual guide data (refreshes every hour)
CACHE = {}
CACHE_TTL = 3600  # 1 hour

# All available visual guides
VISUAL_GUIDES = {
    # DC Lines
    'multiverse': 'https://www.actionfigure411.com/dc/multiverse-visual-guide.php',
    'page_punchers': 'https://www.actionfigure411.com/dc/page-punchers-visual-guide.php',
    'retro_66': 'https://www.actionfigure411.com/dc/retro-66-visual-guide.php',
    'super_powers': 'https://www.actionfigure411.com/dc/mcfarlane-super-powers-visual-guide.php',
    'batman_animated': 'https://www.actionfigure411.com/dc/batman-animated-series-visual-guide.php',
    # MOTU Lines
    'motu_origins': 'https://www.actionfigure411.com/masters-of-the-universe/origins-visual-guide.php',
    'motu_masterverse': 'https://www.actionfigure411.com/masters-of-the-universe/masterverse-visual-guide.php',
}

# Map iOS app line names to visual guide keys
LINE_TO_GUIDES = {
    'DC Multiverse': ['multiverse'],
    'DC Page Punchers': ['page_punchers'],  # Separate line for Page Punchers
    'DC Super Powers': ['super_powers'],
    'DC Retro': ['retro_66', 'batman_animated'],  # Both retro style
    'DC Direct': ['multiverse'],  # Fall back to Multiverse
    'MOTU Origins': ['motu_origins'],
    'MOTU Masterverse': ['motu_masterverse'],
}

# Initialize cache for all guides
for guide in VISUAL_GUIDES:
    CACHE[guide] = {'data': [], 'timestamp': 0}


def fetch_visual_guide(guide_type: str) -> list:
    """Fetch and parse a visual guide page from ActionFigure411"""
    
    urls = VISUAL_GUIDES
    
    url = urls.get(guide_type)
    if not url:
        return []
    
    # Check cache
    cache_entry = CACHE.get(guide_type, {})
    if cache_entry.get('data') and (time.time() - cache_entry.get('timestamp', 0)) < CACHE_TTL:
        logger.info(f"Using cached {guide_type} data ({len(cache_entry['data'])} figures)")
        return cache_entry['data']
    
    logger.info(f"Fetching {guide_type} visual guide from {url}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        # Find all figure entries - they have "enlarge" links with figure images
        # The structure is: text with figure name followed by "enlarge" link
        # Images are in format: /dc/images/figure-name-1234.jpg
        
        # Find all img tags
        for img in soup.find_all('img'):
            src = img.get('src', '')
            
            # Check if it's a figure image (contains /dc/images/ or similar)
            if '/images/' in src and src.endswith('.jpg'):
                # Make absolute URL
                if src.startswith('/'):
                    img_url = f"https://www.actionfigure411.com{src}"
                elif not src.startswith('http'):
                    img_url = f"https://www.actionfigure411.com/{src}"
                else:
                    img_url = src
                
                # Convert thumbnail to full-size image
                img_url = img_url.replace('/images/thumbs/', '/images/')
                
                # Get alt text or title for figure name
                alt = img.get('alt', '') or img.get('title', '')
                
                # Try to find figure name from nearby text
                parent = img.find_parent(['td', 'div', 'li', 'article'])
                if parent:
                    text = parent.get_text(separator=' ', strip=True)
                    # Extract figure name (usually before "enlarge" or "add to collection")
                    text = re.sub(r'(enlarge|add to collection).*', '', text, flags=re.IGNORECASE).strip()
                    if text and len(text) > 3:
                        alt = text
                
                if alt and 'DC Multiverse' in alt or 'DC McFarlane' in alt or len(alt) > 5:
                    # Clean up the name
                    name = alt.strip()
                    name = re.sub(r'\s+', ' ', name)
                    
                    results.append({
                        'url': img_url,
                        'title': name,
                        'source': 'ActionFigure411',
                        'source_icon': 'star.fill'
                    })
        
        # Also parse the text-based entries
        # The page has entries like "DC Multiverse Batman (Flashpoint)enlarge"
        text_content = soup.get_text()
        
        # Find patterns like "DC Multiverse Figure Name (Description)enlarge"
        pattern = r'(DC (?:Multiverse|McFarlane DC Page Punchers) [^|]+?)(?=enlarge|add to collection)'
        matches = re.findall(pattern, text_content)
        
        for match in matches:
            name = match.strip()
            if len(name) > 10:
                # Try to find corresponding image
                # Generate possible image filename
                slug = name.lower()
                slug = re.sub(r'^dc (?:multiverse|mcfarlane dc page punchers)\s*', '', slug)
                slug = re.sub(r'[^a-z0-9]+', '-', slug)
                slug = slug.strip('-')
                
                # Check if we already have this figure
                existing = [r for r in results if name.lower() in r['title'].lower()]
                if not existing:
                    results.append({
                        'url': '',  # Will need to be resolved
                        'title': name,
                        'source': 'ActionFigure411',
                        'source_icon': 'star.fill',
                        'slug': slug
                    })
        
        # Remove duplicates
        seen = set()
        unique_results = []
        for r in results:
            key = r['title'].lower()
            if key not in seen and r.get('url'):
                seen.add(key)
                unique_results.append(r)
        
        # Update cache
        CACHE[guide_type] = {'data': unique_results, 'timestamp': time.time()}
        
        logger.info(f"Found {len(unique_results)} figures in {guide_type} guide")
        return unique_results
        
    except Exception as e:
        logger.error(f"Error fetching {guide_type} visual guide: {e}")
        return cache_entry.get('data', [])


def search_actionfigure411(query: str, line: str = None) -> list:
    """Search ActionFigure411 visual guides for matching figures
    
    Args:
        query: Search term
        line: Optional figure line (e.g., 'DC Multiverse') to prioritize results
    """
    results = []
    
    # Determine which guides to search based on line
    if line and line in LINE_TO_GUIDES:
        # Search matching guides first, then others
        priority_guides = LINE_TO_GUIDES[line]
        other_guides = [g for g in VISUAL_GUIDES.keys() if g not in priority_guides]
        guide_order = priority_guides + other_guides
        logger.info(f"Line '{line}' - prioritizing guides: {priority_guides}")
    else:
        guide_order = list(VISUAL_GUIDES.keys())
    
    # Fetch all guides in order
    all_figures = []
    for guide_type in guide_order:
        figures = fetch_visual_guide(guide_type)
        # Tag figures with their guide for priority sorting
        for fig in figures:
            fig['_priority'] = 0 if line and guide_type in LINE_TO_GUIDES.get(line, []) else 1
        all_figures.extend(figures)
    
    if not all_figures:
        logger.warning("No figures in cache, attempting direct fetch")
        return []
    
    # Normalize query for matching - use user's exact terms (e.g. "Mirror Master Platinum")
    query_lower = query.lower().strip()
    query_words = set(re.findall(r'\w+', query_lower))
    # Exclude common filler so we count meaningful terms
    query_words -= {'dc', 'multiverse', 'the', 'of', 'and', 'a', 'an', 'mcfarlane', 'page', 'punchers'}
    
    # Distinct character names that must not be mixed (e.g. Jay Garrick vs Barry Allen)
    # If query has one name and result title has another from same group, exclude the result
    FLASH_NAMES = {'jay', 'garrick', 'barry', 'allen', 'wally', 'west'}
    
    def is_wrong_character(query_words_set, title_lower):
        """Exclude result if user searched for one character but result is a different one (e.g. Jay vs Barry)."""
        title_words_set = set(re.findall(r'\w+', title_lower))
        query_has_jay = 'jay' in query_words_set or 'garrick' in query_words_set
        query_has_barry = 'barry' in query_words_set or 'allen' in query_words_set
        query_has_wally = 'wally' in query_words_set or 'west' in query_words_set
        title_has_jay = 'jay' in title_words_set or 'garrick' in title_words_set
        title_has_barry = 'barry' in title_words_set or 'allen' in title_words_set
        title_has_wally = 'wally' in title_words_set or 'west' in title_words_set
        # If query is clearly one Flash and title is a different Flash, reject
        if query_has_jay and (title_has_barry or title_has_wally) and not title_has_jay:
            return True
        if query_has_barry and (title_has_jay or title_has_wally) and not title_has_barry:
            return True
        if query_has_wally and (title_has_jay or title_has_barry) and not title_has_wally:
            return True
        return False
    
    for fig in all_figures:
        title = fig.get('title', '').lower()
        title_words = set(re.findall(r'\w+', title))
        common = query_words & title_words
        match_count = len(common)
        
        # Exclude wrong character (e.g. search "Jay Garrick" must not return "Barry Allen")
        if is_wrong_character(query_words, title):
            continue
        
        # Include if full query is substring, or any of the user's terms match
        full_substring = query_lower in title
        if full_substring or match_count >= 1:
            fig['_match_count'] = len(query_words) if full_substring else match_count
            fig['_full_match'] = full_substring
            results.append(fig)
            continue
        
        # Fuzzy match on the main character name (for short queries)
        char_name = re.split(r'\s*[\(\-]', title)[0].strip()
        query_char = re.split(r'\s*[\(\-]', query_lower)[0].strip()
        if char_name and query_char and len(query_words) <= 2:
            ratio = SequenceMatcher(None, query_char, char_name).ratio()
            if ratio > 0.7:
                fig['_match_count'] = 1
                fig['_full_match'] = False
                results.append(fig)
    
    # Sort by match quality first (so "Jay Garrick" shows best matches from any line), then line priority
    def relevance_score(fig):
        priority = fig.get('_priority', 1)
        match_count = fig.get('_match_count', 0)
        full_match = fig.get('_full_match', False)
        # Best matches first: most query terms, then full phrase, then prefer figure's line
        return (-match_count, 0 if full_match else 1, priority)
    
    results.sort(key=relevance_score)
    
    # Remove internal fields before returning
    for fig in results:
        fig.pop('_priority', None)
        fig.pop('_match_count', None)
        fig.pop('_full_match', None)
    
    return results[:40]  # Return more so user sees Multiverse and Page Punchers options


def search_legendsverse(query: str) -> list:
    """Search legendsverse.com for figure images"""
    results = []
    try:
        search_url = f'https://legendsverse.com/?s={urllib.parse.quote(query)}'
        response = requests.get(search_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find images from legendsverse media
        imgs = soup.find_all('img', src=lambda x: x and 'media.legendsverse.com' in x)
        
        seen = set()
        for img in imgs[:20]:
            src = img.get('src')
            if not src or src in seen:
                continue
            seen.add(src)
            
            # Keep the original URL - the card/thumb versions are what actually exist
            # Don't try to convert to "full size" as those URLs don't exist
            full_src = src
            
            # Try to get title
            alt = img.get('alt', '') or img.get('title', '')
            parent = img.find_parent('a')
            if parent:
                title = parent.get('title', '') or parent.get_text(strip=True) or alt
            else:
                title = alt or 'LegendsVerse Figure'
            
            if len(title) > 3:
                results.append({
                    'url': full_src,
                    'title': title[:80],
                    'source': 'LegendsVerse',
                    'source_icon': 'globe'
                })
                    
    except Exception as e:
        logger.error(f"Error searching LegendsVerse: {e}")
    
    return results


def fetch_mcfarlane_product_page(product_url: str) -> dict:
    """Fetch a McFarlane product page and extract title + all product images (carousel, etc.).
    
    McFarlane product pages use JS carousels; images may be in img src, data-src,
    og:image, or embedded in script/JSON. Returns { 'title': str, 'images': [url, ...] }.
    """
    if not product_url.strip().startswith('https://mcfarlane.com/'):
        return {'title': '', 'images': [], 'error': 'URL must be https://mcfarlane.com/...'}
    
    try:
        response = requests.get(product_url.strip(), headers=HEADERS, timeout=20)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        
        # Title from h1 or og:title
        title = ''
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            title = og_title['content'].strip()
        if not title:
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text(strip=True)
        
        seen = set()
        images = []
        
        # 1. og:image
        og_img = soup.find('meta', property='og:image')
        if og_img and og_img.get('content'):
            u = og_img['content'].strip()
            if u.startswith('//'):
                u = 'https:' + u
            if u not in seen and ('mcfarlane' in u or 'cdn' in u or 'cloudinary' in u or u.endswith(('.jpg', '.jpeg', '.png', '.webp'))):
                seen.add(u)
                images.append(u)
        
        # 2. All img with src or data-src (product gallery / carousel)
        for img in soup.find_all('img'):
            for attr in ('data-src', 'src'):
                u = img.get(attr)
                if not u or u in seen:
                    continue
                u = u.strip()
                if u.startswith('//'):
                    u = 'https:' + u
                elif u.startswith('/'):
                    u = 'https://mcfarlane.com' + u
                if not u.startswith('http'):
                    continue
                # Prefer product images (skip tiny icons / logos)
                if any(skip in u.lower() for skip in ('logo', 'icon', 'avatar', 'favicon', 'pixel', '1x1')):
                    continue
                if u.endswith(('.jpg', '.jpeg', '.png', '.webp')) or 'mcfarlane' in u or 'cloudinary' in u or 'cdn' in u:
                    seen.add(u)
                    images.append(u)
        
        # 3. Script tags: look for JSON with image URLs (common in WooCommerce / React)
        for script in soup.find_all('script', type=re.compile(r'application/(ld\+)?json')):
            try:
                data = json.loads(script.string or '{}')
                if isinstance(data, dict):
                    for key in ('image', 'images', 'photo', 'gallery', 'src'):
                        val = data.get(key)
                        if isinstance(val, str) and val.startswith('http'):
                            if val not in seen:
                                seen.add(val)
                                images.append(val)
                        elif isinstance(val, list):
                            for item in val:
                                url = item if isinstance(item, str) else (item.get('url') or item.get('src') or item.get('image'))
                                if url and isinstance(url, str) and url.startswith('http') and url not in seen:
                                    seen.add(url)
                                    images.append(url)
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            url = item.get('url') or item.get('src') or item.get('image')
                            if url and isinstance(url, str) and url.startswith('http') and url not in seen:
                                seen.add(url)
                                images.append(url)
            except (json.JSONDecodeError, TypeError):
                pass
        
        # 4. Inline script: look for URLs matching common CDN patterns
        for script in soup.find_all('script'):
            if not script.string:
                continue
            # Match "https://...mcfarlane.../...jpg" or cloudinary/cdn URLs
            for m in re.findall(r'https?://[^\s"\'<>]+\.(?:jpg|jpeg|png|webp)', script.string, re.I):
                m = m.rstrip('.,;:)')
                if m not in seen and 'logo' not in m.lower() and 'icon' not in m.lower():
                    seen.add(m)
                    images.append(m)
        
        return {'title': title, 'images': images}
        
    except requests.RequestException as e:
        logger.error(f"Error fetching McFarlane product page: {e}")
        return {'title': '', 'images': [], 'error': str(e)}
    except Exception as e:
        logger.error(f"Error parsing McFarlane product page: {e}")
        return {'title': '', 'images': [], 'error': str(e)}


def search_google_images(query: str) -> list:
    """Search Google Images (limited, may be blocked)"""
    results = []
    try:
        search_url = f"https://www.google.com/search?tbm=isch&q={urllib.parse.quote(query + ' mcfarlane action figure')}"
        response = requests.get(search_url, headers=HEADERS, timeout=15)
        
        # Extract image URLs from the response
        img_urls = re.findall(r'"(https://[^"]+\.(?:jpg|jpeg|png|webp))"', response.text)
        
        seen = set()
        for url in img_urls[:15]:
            if 'google' not in url and 'gstatic' not in url and url not in seen:
                seen.add(url)
                results.append({
                    'url': url,
                    'title': f'{query} - Google Image',
                    'source': 'Google',
                    'source_icon': 'magnifyingglass'
                })
                
    except Exception as e:
        logger.error(f"Error searching Google Images: {e}")
    
    return results


@app.route('/api/search', methods=['GET'])
def search_images():
    """
    Search all sources for action figure images
    
    Query params:
    - q: Search query (required)
    - sources: Comma-separated list of sources (optional, default: all)
    - line: Figure line name (optional, e.g., 'DC Multiverse') to prioritize results
    """
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Query parameter "q" is required'}), 400
    
    sources_param = request.args.get('sources', 'all').lower()
    line_param = request.args.get('line', '').strip()  # e.g., 'DC Multiverse'
    
    logger.info(f"Search: q='{query}', sources={sources_param}, line='{line_param}'")
    
    all_results = []
    
    # Use ThreadPoolExecutor for parallel searches
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {}
        
        if sources_param == 'all' or 'actionfigure411' in sources_param:
            futures[executor.submit(search_actionfigure411, query, line_param)] = 'actionfigure411'
        
        # LegendsVerse disabled - URLs are unreliable
        # if sources_param == 'all' or 'legendsverse' in sources_param:
        #     futures[executor.submit(search_legendsverse, query)] = 'legendsverse'
        
        if sources_param == 'all' or 'google' in sources_param:
            futures[executor.submit(search_google_images, query)] = 'google'
        
        for future in as_completed(futures):
            source_name = futures[future]
            try:
                results = future.result()
                all_results.extend(results)
                logger.info(f"Found {len(results)} results from {source_name}")
            except Exception as e:
                logger.error(f"Error from {source_name}: {e}")
    
    # Remove duplicates by URL
    seen_urls = set()
    unique_results = []
    for result in all_results:
        url = result.get('url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_results.append(result)
    
    return jsonify({
        'query': query,
        'count': len(unique_results),
        'results': unique_results
    })


@app.route('/api/mcfarlane-product', methods=['GET'])
def mcfarlane_product():
    """
    Fetch images from a McFarlane product page URL (e.g. new figures not yet on ActionFigure411).
    
    Query params:
    - url: Full McFarlane product URL (required), e.g. https://mcfarlane.com/toys/flash-jay-garrick-flash-123-comic-red-platinum-edition/
    
    Returns: { title, images: [url, ...], error? }
    """
    product_url = request.args.get('url', '').strip()
    if not product_url:
        return jsonify({'error': 'Query parameter "url" is required', 'title': '', 'images': []}), 400
    
    result = fetch_mcfarlane_product_page(product_url)
    if result.get('error') and not result.get('images'):
        return jsonify(result), 422
    return jsonify({k: v for k, v in result.items() if k != 'error'})


@app.route('/api/refresh-cache', methods=['POST'])
def refresh_cache():
    """Force refresh of the visual guide cache"""
    global CACHE
    CACHE = {guide: {'data': [], 'timestamp': 0} for guide in VISUAL_GUIDES.keys()}
    
    # Pre-fetch all guides
    counts = {}
    for guide_type in VISUAL_GUIDES.keys():
        data = fetch_visual_guide(guide_type)
        counts[guide_type] = len(data)
    
    return jsonify({
        'status': 'ok',
        'counts': counts,
        'total': sum(counts.values())
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    cache_counts = {guide: len(CACHE.get(guide, {}).get('data', [])) for guide in VISUAL_GUIDES.keys()}
    return jsonify({
        'status': 'ok',
        'service': 'ActionFigure Image Search',
        'cache': cache_counts,
        'total_figures': sum(cache_counts.values())
    })


if __name__ == '__main__':
    print("=" * 50)
    print("Action Figure Image Search API")
    print("=" * 50)
    print("Starting server on http://localhost:5050")
    print("API Endpoints:")
    print("  GET  /api/search?q=<query>  - Search for images")
    print("  GET  /api/mcfarlane-product?url=<mcfarlane product URL>  - Get images from McFarlane product page")
    print("  POST /api/refresh-cache     - Refresh visual guide cache")
    print("  GET  /api/health            - Health check")
    print("=" * 50)
    
    # Pre-load cache on startup
    print("Pre-loading visual guide cache...")
    total = 0
    for guide_type, url in VISUAL_GUIDES.items():
        data = fetch_visual_guide(guide_type)
        print(f"  - {guide_type}: {len(data)} figures")
        total += len(data)
    print(f"Cache loaded! Total: {total} figures")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5050, debug=True)
