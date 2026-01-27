#!/usr/bin/env python3
"""
Fix remaining figures that didn't match automatically.
Maps our figure names to actionfigure411.com names.
"""

import json
import urllib.request

JSON_FILE = r'c:\Code\ActionFigureTracker\Models\all_figures.json'
SCRAPED_FILE = r'c:\Code\ActionFigureTracker\downloaded_images\scraped_figures.json'

# Manual mapping: our name -> scraped name (key in scraped_figures.json)
MANUAL_MAPPING = {
    "Batman Beyond (Terry McGinnis)": "batman batman beyond",
    "Batwoman Beyond": "batwoman unmasked batman beyond",
    "Blight": "blight batman beyond futures end",
    "Cyborg (Ray Fisher)": "cyborg justice league",
    "Darkseid (Megafig)": "darkseid justice league",
    "Flash (Ezra Miller)": "flash justice league",
    "Steppenwolf (Megafig)": "steppenwolf justice league",
    "Polka-Dot Man": "polka dot man the suicide squad",
    "Barry Allen": "barry allen speed metal",
    "Jay Garrick": "jay garrick speed metal",
    "Joker (Ledger)": "joker the dark knight trilogy",
    "Captain Boomerang": "captain boomerang the flash",
    "Starfire": "starfire dc rebirth",
    "Green Lantern (Alan Scott)": "green lantern alan scott day of vengeance",
    "Penguin (Classic)": "the penguin dc classic",
    "Sinestro (Classic)": "sinestro sinestro corps war",
    "The Spectre": "the spectre gold label crisis on infinite earth",
    "Blackhawk": "blackhawk dc classics",
    "Elongated Man": "elongated man dc classics",
    "Batwing (Megafig)": "batwing gold label the flash movie",
    "Dark Flash": "dark flash the flash movie",
    "Kid Flash (Wallace West)": "kid flash teen titans",
    "Penguin (Arkham City)": "the penguin",
    "Penguin (Colin Farrell)": "penguin the batman",
    "Riddler (Paul Dano)": "riddler the batman",
    "King Kordax": "king kordax the lost kingdom",
    "Scarecrow (Murphy)": None,  # Not in database
    "Storm (Seahorse)": None,  # Not in database - was incorrectly matched to firestorm
    "Supergirl (Sasha Calle)": "supergirl the flash movie",
    "Batgirl (Silverstone)": "batgirl batman robin",
    "Monitor": "the monitor baf",
    "Poison Ivy (Thurman)": "poison ivy batman robin",
    "Psycho Pirate": "psycho pirate gold label crisis on infinite earth",
    "Robin (O'Donnell)": "robin batman forever",
    "Green Arrow (Longbow Hunter)": None,  # Not in database
    "Superman (False God)": "superman false god batman vs superman platinum edition",
    "Superman (JLA - Electric Blue)": "superman jla",
    "Black Lantern Superman": "black lantern superman blackest night",
    "Deathstorm": "deathstorm blackest night",
    "Omega (Last Knight)": "omega last knight on earth 3",
    "Zatanna with Detective Chimp": None,
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}


def check_image_exists(url: str) -> bool:
    """Check if an image URL exists"""
    try:
        req = urllib.request.Request(url, headers=HEADERS, method='HEAD')
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status == 200
    except:
        return False


def main():
    # Load our figures
    print(f"Loading figures from {JSON_FILE}...")
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        all_figures = json.load(f)
    
    # Load scraped data
    print(f"Loading scraped data from {SCRAPED_FILE}...")
    with open(SCRAPED_FILE, 'r', encoding='utf-8') as f:
        scraped = json.load(f)
    
    # Find figures that still need images
    still_missing = []
    for fig in all_figures:
        if fig.get('series') == 'dc-multiverse' and not fig.get('imageString'):
            still_missing.append(fig)
    
    print(f"Found {len(still_missing)} figures still missing images")
    
    # Try to match using manual mapping
    updated = 0
    failed = []
    
    for fig in still_missing:
        name = fig['name']
        print(f"\nProcessing: {name}")
        
        if name in MANUAL_MAPPING:
            scraped_key = MANUAL_MAPPING[name]
            if scraped_key is None:
                print(f"  [SKIP] Marked as not available")
                failed.append({'name': name, 'reason': 'Not available on site'})
                continue
                
            if scraped_key in scraped:
                image_url = scraped[scraped_key]['image_url']
                print(f"  Mapped to: {scraped_key}")
                print(f"  Image URL: {image_url}")
                
                if check_image_exists(image_url):
                    fig['imageString'] = image_url
                    updated += 1
                    print(f"  [OK] Updated")
                else:
                    print(f"  [FAIL] Image not accessible")
                    failed.append({'name': name, 'reason': 'Image not accessible', 'url': image_url})
            else:
                print(f"  [FAIL] Mapped key '{scraped_key}' not in scraped data")
                # Try fuzzy search
                found = False
                for key in scraped.keys():
                    if scraped_key.replace(' ', '') in key.replace(' ', ''):
                        print(f"  Found similar: {key}")
                        image_url = scraped[key]['image_url']
                        if check_image_exists(image_url):
                            fig['imageString'] = image_url
                            updated += 1
                            found = True
                            print(f"  [OK] Updated with similar match")
                            break
                if not found:
                    failed.append({'name': name, 'reason': f'Mapped key not found: {scraped_key}'})
        else:
            print(f"  [SKIP] No manual mapping")
            failed.append({'name': name, 'reason': 'No manual mapping'})
    
    # Save updated JSON
    print(f"\nSaving updated figures...")
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_figures, f, indent=2)
    
    # Summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"Still missing before: {len(still_missing)}")
    print(f"Successfully updated: {updated}")
    print(f"Failed: {len(failed)}")
    
    if failed:
        print("\nStill failed:")
        for f in failed:
            print(f"  - {f['name']}: {f['reason']}")


if __name__ == '__main__':
    main()
