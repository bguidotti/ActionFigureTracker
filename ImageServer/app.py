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
    'DC Multiverse': ['multiverse', 'page_punchers'],  # Page Punchers are part of Multiverse
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
    
    # Normalize query for matching
    query_lower = query.lower()
    query_words = set(re.findall(r'\w+', query_lower))
    
    for fig in all_figures:
        title = fig.get('title', '').lower()
        
        # Direct substring match
        if query_lower in title:
            results.append(fig)
            continue
        
        # Word overlap match
        title_words = set(re.findall(r'\w+', title))
        common_words = query_words & title_words
        # Exclude common filler words
        common_words -= {'dc', 'multiverse', 'the', 'of', 'and', 'a', 'an', 'mcfarlane', 'page', 'punchers'}
        
        if len(common_words) >= 2:
            results.append(fig)
            continue
        
        # Fuzzy match on the main character name
        # Extract character name (first part before parentheses)
        char_name = re.split(r'\s*[\(\-]', title)[0].strip()
        query_char = re.split(r'\s*[\(\-]', query_lower)[0].strip()
        
        if char_name and query_char:
            ratio = SequenceMatcher(None, query_char, char_name).ratio()
            if ratio > 0.7:
                results.append(fig)
    
    # Sort by relevance (matching line first, then exact matches)
    def relevance_score(fig):
        priority = fig.get('_priority', 1)  # 0 = matching line, 1 = other
        title = fig.get('title', '').lower()
        exact_match = 0 if query_lower in title else 1
        # Remove the internal priority field before returning
        if '_priority' in fig:
            del fig['_priority']
        return (priority, exact_match)
    
    results.sort(key=relevance_score)
    
    return results[:30]  # Limit to 30 results


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
