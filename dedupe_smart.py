import json
import csv
import re
from difflib import SequenceMatcher

# --- CONFIGURATION ---
JSON_FILE = 'Models/all_figures.json'      # Your current mixed file
WIKI_FILE = 'wikipedia_list.csv'           # The new source of truth
OUTPUT_FILE = 'Models/all_figures_clean.json'

def normalize(text):
    """Normalize text for fuzzy comparison (lowercase, remove punctuation)."""
    if not text: return ""
    # Remove 'version' from descriptions (e.g., "Detective Comics #1000 version")
    text = re.sub(r'\s+version$', '', text, flags=re.IGNORECASE)
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)  # Remove special chars
    return " ".join(text.split())

def construct_name(figure, description):
    """Builds a standard name like 'Batman (Detective Comics #1000)'."""
    clean_desc = re.sub(r'\s+version$', '', description, flags=re.IGNORECASE).strip()
    clean_fig = figure.strip()
    
    if not clean_desc:
        return clean_fig
    
    # If description is just a variant note, append it in parens
    return f"{clean_fig} ({clean_desc})"

def load_wiki_data():
    """Parses the structured Wiki CSV, handling 'blank means same as above' logic."""
    print(f"📖 Reading {WIKI_FILE}...")
    
    checklist = {} # Map normalized_name -> {year, name, is_platinum}
    
    last_release = "2020"
    last_figure = "Unknown"
    
    with open(WIKI_FILE, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f)
        
        for row in reader:
            # Skip empty rows or headers
            if not row or len(row) < 4 or "Release" in row[0]:
                continue
                
            # Extract columns
            release = row[0].strip()
            figure = row[1].strip()
            desc = row[3].strip()
            
            # 1. Handle "Same as above" logic
            if release:
                last_release = release
            else:
                release = last_release # Inherit year
                
            if figure:
                last_figure = figure
            else:
                figure = last_figure # Inherit figure name (for variants)
            
            # 2. Build the full name
            full_name = construct_name(figure, desc)
            norm_name = normalize(full_name)
            
            # 3. Extract Year (e.g., "Q1 2020" -> 2020)
            year_match = re.search(r'202[0-9]', release)
            year = int(year_match.group(0)) if year_match else 2020
            
            # 4. Store
            checklist[norm_name] = {
                "official_name": full_name,
                "year": year,
                "is_platinum": "platinum" in desc.lower() or "chase" in desc.lower()
            }
            
    print(f"✅ Loaded {len(checklist)} unique figures from Wiki.")
    return checklist

def dedupe():
    # 1. Load Data
    wiki_data = load_wiki_data()
    
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Could not find {JSON_FILE}. Make sure path is correct.")
        return

    clean_list = []
    seen_names = {} # Map normalized_name -> index_in_clean_list
    
    stats = {'total': len(raw_data), 'merged': 0, 'removed': 0, 'kept': 0}
    print(f"🔍 Analyzing {stats['total']} figures...")

    for item in raw_data:
        # Normalize the name from the JSON
        name = item.get('name', 'Unknown')
        norm_name = normalize(name)
        
        # --- SCORE THE IMAGE ---
        # 2 = ActionFigure411 (Target), 1 = Legendsverse, 0 = None
        img_url = item.get('imageString', '')
        img_score = 0
        if 'actionfigure411' in img_url: img_score = 2
        elif 'legendsverse' in img_url: img_score = 1
        
        # Check if we already have this figure
        if norm_name in seen_names:
            existing_idx = seen_names[norm_name]
            existing_item = clean_list[existing_idx]
            
            # Score the existing one
            existing_img = existing_item.get('imageString', '')
            existing_score = 0
            if 'actionfigure411' in existing_img: existing_score = 2
            elif 'legendsverse' in existing_img: existing_score = 1
            
            # DECISION: Who wins?
            if img_score > existing_score:
                # NEW one wins (better image). 
                # Preserve 'isCollected' status if the old one had it true.
                was_collected = existing_item.get('isCollected', False)
                item['isCollected'] = was_collected or item.get('isCollected', False)
                
                # Replace it
                clean_list[existing_idx] = item
                stats['merged'] += 1
            else:
                # OLD one wins. Ignore this new duplicate.
                stats['removed'] += 1
                continue
        else:
            # It's new! Add it.
            clean_list.append(item)
            seen_names[norm_name] = len(clean_list) - 1
            
        # --- ENRICH WITH WIKI DATA ---
        # Now that we've decided to keep 'item', let's fix its year/name if possible
        if norm_name in wiki_data:
            meta = wiki_data[norm_name]
            # If JSON is missing year, add it
            if not item.get('year'):
                item['year'] = meta['year']
            # If JSON name is messy, use official Wiki name? (Optional, maybe risky)
            # item['name'] = meta['official_name'] 
            
            # Tag Platinums if not already
            if meta['is_platinum'] and 'Platinum' not in item['name']:
                item['name'] = item['name'] + " (Platinum)"

    stats['kept'] = len(clean_list)
    
    print("-" * 30)
    print(f"📊 Final Results:")
    print(f"   Original: {stats['total']}")
    print(f"   Cleaned:  {stats['kept']}")
    print(f"   Removed:  {stats['removed']} duplicates")
    print("-" * 30)

    # Save
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(clean_list, f, indent=2)
    print(f"💾 Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    dedupe()