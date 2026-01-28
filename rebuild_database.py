import json
import csv
import re
from difflib import SequenceMatcher

# --- FILES ---
WIKI_FILE = 'wikipedia_list.csv'           # The Source of Truth
JSON_SOURCE = 'all_figures.json.backup'    # The "Parts Bin" (Images/Status)
OUTPUT_FILE = 'Models/all_figures_clean.json'

def normalize(text):
    """Simplifies text for comparison (e.g., 'Batman: Arkham' -> 'batmanarkham')."""
    if not text: return ""
    # Remove common filler words to help matching
    text = re.sub(r'\(.*?\)', '', text) # Remove text in parens for broad matching first
    text = text.lower()
    text = re.sub(r'[^a-z0-9]', '', text)
    return text

def get_best_match(wiki_name, json_data):
    """Finds the best matching figure in the JSON data."""
    best_score = 0
    best_item = None
    
    # We prioritize ActionFigure411 images if scores are similar
    norm_wiki = normalize(wiki_name)
    
    for item in json_data:
        # Skip items that are likely wrong lines (Star Wars, Marvel)
        if 'dc' not in item.get('series', '').lower():
            continue

        item_name = item.get('name', '')
        norm_item = normalize(item_name)
        
        # 1. Exact Match Check (High Confidence)
        if norm_wiki == norm_item:
            score = 100
        else:
            # 2. Fuzzy Match
            score = SequenceMatcher(None, norm_wiki, norm_item).ratio() * 100
        
        # Bonus for "Platinum" matching
        if "platinum" in wiki_name.lower() and "platinum" in item_name.lower():
            score += 10
        elif "platinum" in wiki_name.lower() and "platinum" not in item_name.lower():
            score -= 20 # Penalize mismatching editions
            
        # Bonus for Image Source (ActionFigure411 > Legendsverse)
        img = item.get('imageString', '')
        if 'actionfigure411' in img:
            score += 5
            
        if score > 85 and score > best_score:
            best_score = score
            best_item = item
            
    return best_item

def run_rebuild():
    print("🚀 Starting Database Rebuild...")
    
    # 1. Load the Old Data (Images/Status)
    try:
        with open(JSON_SOURCE, 'r', encoding='utf-8') as f:
            source_data = json.load(f)
        print(f"📦 Loaded {len(source_data)} source records.")
    except Exception as e:
        print(f"❌ Error loading JSON source: {e}")
        return

    new_database = []
    
    # Context pointers for the CSV (Handling "Same as above" logic)
    last_year = "2020"
    last_figure_name = "Unknown"
    
    # 2. Iterate the Master List (Wikipedia CSV)
    with open(WIKI_FILE, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f)
        
        # Skip header rows until we hit data
        start_reading = False
        
        for row in reader:
            if not row: continue
            
            # Detect Header Row to start reading
            if "Release" in row[0] and "Figure" in row[1]:
                start_reading = True
                continue
            if not start_reading: continue
            
            # Extract CSV Columns
            # [0] Release, [1] Figure, [2] Accessories, [3] Description
            col_release = row[0].strip()
            col_figure = row[1].strip()
            col_desc = row[3].strip() if len(row) > 3 else ""
            
            # --- CONTEXT LOGIC ---
            # If Release is empty, use last seen
            if col_release:
                year_match = re.search(r'202[0-9]', col_release)
                if year_match:
                    last_year = year_match.group(0)
            
            # If Figure Name is empty, use last seen (It's a variant/platinum)
            if col_figure:
                last_figure_name = col_figure
            
            # Build the "Official Name"
            # Format: "Batman (Detective Comics #1000)" or "Joker (Arkham Asylum - Bronze Platinum)"
            full_name = last_figure_name
            if col_desc:
                # Clean up description
                clean_desc = col_desc.replace("version", "").strip()
                if clean_desc:
                    full_name += f" ({clean_desc})"
            
            # Platinum Tagging
            if "platinum" in col_desc.lower() or "chase" in col_desc.lower() or "bronze" in col_desc.lower():
                if "Platinum" not in full_name:
                    full_name += " [Platinum]"

            # 3. Find Matches
            match = get_best_match(full_name, source_data)
            
            new_entry = {
                "id": 20000 + len(new_database), # Generate fresh IDs to ensure order
                "name": full_name,
                "series": "dc-multiverse",
                "year": int(last_year),
                "wave": col_release if col_release else "Wave " + last_year,
                "imageString": match['imageString'] if match else "",
                "isCollected": match['isCollected'] if match else False
            }
            
            new_database.append(new_entry)

    # 3. Save
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_database, f, indent=2)
        
    print("-" * 30)
    print(f"✅ REBUILD COMPLETE")
    print(f"   Original Source Entries: {len(source_data)}")
    print(f"   New Database Count:      {len(new_database)}")
    print(f"   (Should match Wiki row count approx 1142)")
    print("-" * 30)

if __name__ == "__main__":
    run_rebuild()