#!/usr/bin/env python3
"""
Merge CSV data into all_figures.json
- Fills in missing IDs, dates, waves
- Adds new figures that don't exist
- Fixes date ordering
- Avoids duplicates
"""

import json
import csv
import re
from datetime import datetime
from typing import Dict, List, Optional

def normalize_name(name: str) -> str:
    """Normalize figure name for comparison (remove extra spaces, case insensitive)"""
    # Remove extra whitespace and normalize
    name = re.sub(r'\s+', ' ', name.strip())
    # Remove common variations
    name = name.replace(' (Chase)', '').replace(' Platinum', '').replace(' Platinum (Chase)', '')
    # Normalize punctuation variations
    name = name.replace(':', ' ').replace('(', ' ').replace(')', ' ')
    # Remove extra spaces
    name = re.sub(r'\s+', ' ', name)
    return name.lower().strip()

def normalize_series(series: str) -> str:
    """Convert series name to JSON format (lowercase with hyphens)"""
    # Map CSV series names to JSON format
    series_map = {
        'DC Multiverse': 'dc-multiverse',
        'DC Super Powers': 'dc-super-powers',
        'DC Retro': 'dc-retro',
        'DC Direct': 'dc-direct',
        'MOTU Origins': 'masters-of-the-universe-origins',
        'MOTU Masterverse': 'masters-of-the-universe-masterverse',
        'Marvel Legends': 'marvel-legends',
        'Star Wars Black Series': 'star-wars-black-series',
        'Page Punchers': 'dc-multiverse'  # Page Punchers are DC Multiverse sub-line
    }
    return series_map.get(series, series.lower().replace(' ', '-'))

def create_date_from_year(year: int) -> str:
    """Create a date string from year (January 1st of that year)"""
    return f"{year}-01-01T00:00:00Z"

def load_existing_json(filepath: str) -> List[Dict]:
    """Load existing JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"WARNING: File not found: {filepath}")
        return []
    except json.JSONDecodeError as e:
        print(f"ERROR: Error parsing JSON: {e}")
        return []

def load_csv_data(csv_string: str = None, csv_file: str = None) -> List[Dict]:
    """Parse CSV data from string or file"""
    if csv_file:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    elif csv_string:
        reader = csv.DictReader(csv_string.strip().split('\n'))
        return list(reader)
    else:
        return []

def find_existing_figure(figures: List[Dict], csv_name: str) -> Optional[Dict]:
    """Find existing figure by normalized name with fuzzy matching"""
    normalized_csv = normalize_name(csv_name)
    
    # Try exact match first
    for fig in figures:
        fig_name = normalize_name(fig.get('name', ''))
        if fig_name == normalized_csv:
            return fig
    
    # Try partial match (for variations like "Batman: Detective Comics #1000" vs "Batman (Detective Comics #1000)")
    # Extract key parts (character name and key identifier)
    csv_parts = set(normalized_csv.split())
    for fig in figures:
        fig_name = normalize_name(fig.get('name', ''))
        fig_parts = set(fig_name.split())
        # If most words match, consider it a match
        if len(csv_parts) > 0 and len(fig_parts) > 0:
            overlap = len(csv_parts & fig_parts) / max(len(csv_parts), len(fig_parts))
            if overlap > 0.7:  # 70% word overlap
                return fig
    
    return None

def get_next_id(figures: List[Dict]) -> int:
    """Get the next available ID"""
    if not figures:
        return 1
    
    max_id = max((fig.get('id', 0) for fig in figures), default=0)
    return max_id + 1

def merge_data(existing_figures: List[Dict], csv_data: List[Dict]) -> List[Dict]:
    """Merge CSV data into existing figures"""
    updated_count = 0
    new_count = 0
    
    # First pass: update existing figures with missing data
    for csv_row in csv_data:
        year = int(csv_row['Year'])
        wave = csv_row['Wave'].strip() if csv_row.get('Wave') and csv_row['Wave'].strip() else None
        name = csv_row['Name'].strip() if csv_row.get('Name') else ''
        series_str = csv_row.get('Series', '').strip() if csv_row.get('Series') else ''
        if not series_str:
            continue  # Skip rows without series
        series = normalize_series(series_str)
        
        # Find matching existing figure
        existing = find_existing_figure(existing_figures, name)
        
        if existing:
            # Update existing figure
            updated = False
            # Update series if it matches (or is missing/wrong)
            if not existing.get('series') or existing.get('series') == 'dc-multiverse':
                existing['series'] = series
                updated = True
            # Add year if not present
            if 'year' not in existing:
                existing['year'] = year
                updated = True
            # Add wave if not present
            if 'wave' not in existing and wave:
                existing['wave'] = wave
                updated = True
            if updated:
                updated_count += 1
        else:
            # Create new figure (only if we have a name)
            if name:
                new_id = get_next_id(existing_figures)
                new_fig = {
                    'id': new_id,
                    'name': name,
                    'series': series,
                    'imageString': '',  # Will need to be filled in later or scraped
                    'isCollected': False,
                    'year': year
                }
                if wave:
                    new_fig['wave'] = wave
                existing_figures.append(new_fig)
                new_count += 1
    
    # Sort by year (for date ordering)
    def get_year(fig: Dict) -> int:
        return fig.get('year', 9999)  # Put items without year at end
    
    # Also sort by name within same year for consistency
    def sort_key(fig: Dict) -> tuple:
        year = fig.get('year', 9999)
        name = fig.get('name', '').lower()
        return (year, name)
    
    existing_figures.sort(key=sort_key)
    
    print(f"   Updated {updated_count} existing figures")
    print(f"   Added {new_count} new figures")
    
    return existing_figures

def main():
    import sys
    import os
    
    # CSV file path from user (or use command line arg)
    csv_file_path = None
    if len(sys.argv) > 1:
        csv_file_path = sys.argv[1]
    else:
        # Try the provided path
        possible_paths = [
            r'\\tsclient\Downloads\DC_Multiverse.csv',
            r'C:\Users\guido\Downloads\DC_Multiverse.csv',
            r'DC_Multiverse.csv'  # Current directory
        ]
        for path in possible_paths:
            if os.path.exists(path):
                csv_file_path = path
                break
    
    # CSV data from user (fallback if file not found)
    csv_data_str = """Year,Wave,Name,Series
2020,Wave 1,Batman (Detective Comics #1000),DC Multiverse
2020,Wave 1,Superman (Action Comics #1000),DC Multiverse
2020,Wave 1,Batman (Animated Series),DC Multiverse
2020,Wave 1,Superman (Animated Series),DC Multiverse
2020,Wave 1,Green Arrow (Arrow TV),DC Multiverse
2020,Wave 1,Harley Quinn (Classic),DC Multiverse
2020,Wave 1,Green Lantern (Justice League Animated),DC Multiverse
2020,Wave 1,Nightwing (Better Than Batman),DC Multiverse
2020,Wave 1,Batgirl (Art of the Crime),DC Multiverse
2020,Wave 1,Batman (Hellbat Suit),DC Multiverse
2020,Wave 1,Superman (Unchained Armor),DC Multiverse
2020,Wave 1,Batman Who Laughs,DC Multiverse
2020,Wave 2,Wonder Woman (1984),DC Multiverse
2020,Wave 2,Wonder Woman (Gold Armor 1984),DC Multiverse
2020,Wave 2,Joker (Arkham Asylum),DC Multiverse
2020,Wave 2,Batman (Arkham Asylum),DC Multiverse
2020,Wave 2,Batman (White Knight),DC Multiverse
2020,Wave 2,Joker (White Knight),DC Multiverse
2020,Wave 2,Azrael (White Knight),DC Multiverse
2020,Wave 3,Flash (Rebirth),DC Multiverse
2020,Wave 3,Cyborg (Teen Titans Animated),DC Multiverse
2020,Wave 3,Azrael (Batman Armor),DC Multiverse
2020,Wave 3,Deathstroke (Arkham Origins),DC Multiverse
2020,Wave 3,Batman (Arkham Knight),DC Multiverse
2020,Merciless BAF,Batman (Dark Nights Metal),DC Multiverse
2020,Merciless BAF,Superman (The Infected),DC Multiverse
2020,Merciless BAF,Batman Who Laughs (Sky Tyrant Wings),DC Multiverse
2020,Merciless BAF,Robin (Earth-22),DC Multiverse
2021,Dark Father BAF,Batman (Death Metal),DC Multiverse
2021,Dark Father BAF,Superman (Death Metal),DC Multiverse
2021,Dark Father BAF,Wonder Woman (Death Metal),DC Multiverse
2021,Dark Father BAF,Robin King (Death Metal),DC Multiverse
2021,Last Knight BAF,Batman (Last Knight on Earth),DC Multiverse
2021,Last Knight BAF,Wonder Woman (Mohawk),DC Multiverse
2021,Last Knight BAF,Scarecrow (Last Knight),DC Multiverse
2021,Last Knight BAF,Omega (Last Knight),DC Multiverse
2021,ZSJL Wave,Batman (Tactical Suit),DC Multiverse
2021,ZSJL Wave,Superman (Black Suit),DC Multiverse
2021,ZSJL Wave,Flash (Ezra Miller),DC Multiverse
2021,ZSJL Wave,Aquaman (Jason Momoa),DC Multiverse
2021,ZSJL Wave,Cyborg (Ray Fisher),DC Multiverse
2021,ZSJL Wave,Steppenwolf (Megafig),DC Multiverse
2021,ZSJL Wave,Darkseid (Megafig),DC Multiverse
2021,Suicide Squad BAF,Harley Quinn (Movie),DC Multiverse
2021,Suicide Squad BAF,Bloodsport,DC Multiverse
2021,Suicide Squad BAF,Peacemaker,DC Multiverse
2021,Suicide Squad BAF,Polka-Dot Man,DC Multiverse
2021,King Shark BAF,King Shark (Megafig),DC Multiverse
2021,Three Jokers,Batman (Three Jokers),DC Multiverse
2021,Three Jokers,Red Hood (Three Jokers),DC Multiverse
2021,Three Jokers,Batgirl (Three Jokers),DC Multiverse
2021,Three Jokers,The Clown Joker,DC Multiverse
2021,Three Jokers,The Criminal Joker,DC Multiverse
2021,Three Jokers,The Comedian Joker,DC Multiverse
2021,Batman Beyond,Batman Beyond (Terry McGinnis),DC Multiverse
2021,Batman Beyond,Shriek,DC Multiverse
2021,Batman Beyond,Batwoman Beyond,DC Multiverse
2021,Batman Beyond,Blight,DC Multiverse
2022,The Batman Movie,Batman (Robert Pattinson),DC Multiverse
2022,The Batman Movie,Catwoman (Zoe Kravitz),DC Multiverse
2022,The Batman Movie,Penguin (Colin Farrell),DC Multiverse
2022,The Batman Movie,Riddler (Paul Dano),DC Multiverse
2022,The Batman Movie,Bruce Wayne (Drifter),DC Multiverse
2022,Black Adam Movie,Black Adam (The Rock),DC Multiverse
2022,Black Adam Movie,Hawkman,DC Multiverse
2022,Black Adam Movie,Dr. Fate,DC Multiverse
2022,Black Adam Movie,Cyclone,DC Multiverse
2022,Black Adam Movie,Atom Smasher,DC Multiverse
2022,Black Adam Movie,Sabbac (Megafig),DC Multiverse
2022,Speed Metal BAF,Flash (Wally West),DC Multiverse
2022,Speed Metal BAF,Kid Flash (Wallace West),DC Multiverse
2022,Speed Metal BAF,Barry Allen,DC Multiverse
2022,Speed Metal BAF,Jay Garrick,DC Multiverse
2022,Atrocitus BAF,Black Lantern Superman,DC Multiverse
2022,Atrocitus BAF,Black Lantern Batman,DC Multiverse
2022,Atrocitus BAF,Deathstorm,DC Multiverse
2022,Atrocitus BAF,Kyle Rayner (Green Lantern),DC Multiverse
2022,Arkham City BAF,Batman (Arkham City),DC Multiverse
2022,Arkham City BAF,Catwoman (Arkham City),DC Multiverse
2022,Arkham City BAF,Penguin (Arkham City),DC Multiverse
2022,Arkham City BAF,Ra's Al Ghul (Arkham City),DC Multiverse
2023,Flash Movie,Batman (Michael Keaton),DC Multiverse
2023,Flash Movie,Batman (Ben Affleck),DC Multiverse
2023,Flash Movie,Flash (Ezra Miller),DC Multiverse
2023,Flash Movie,Supergirl (Sasha Calle),DC Multiverse
2023,Flash Movie,Dark Flash,DC Multiverse
2023,Flash Movie,Batwing (Megafig),DC Multiverse
2023,Beast Boy BAF,Nightwing (Titans),DC Multiverse
2023,Beast Boy BAF,Raven (Titans),DC Multiverse
2023,Beast Boy BAF,Donna Troy (Titans),DC Multiverse
2023,Beast Boy BAF,Arsenal (Titans),DC Multiverse
2023,Dark Knight Trilogy BAF,Batman (Bale),DC Multiverse
2023,Dark Knight Trilogy BAF,Joker (Ledger),DC Multiverse
2023,Dark Knight Trilogy BAF,Two-Face (Eckhart),DC Multiverse
2023,Dark Knight Trilogy BAF,Scarecrow (Murphy),DC Multiverse
2023,Aquaman 2 BAF,Aquaman (Stealth Suit),DC Multiverse
2023,Aquaman 2 BAF,Black Manta,DC Multiverse
2023,Aquaman 2 BAF,King Kordax,DC Multiverse
2023,Aquaman 2 BAF,Storm (Seahorse),DC Multiverse
2024,Plastic Man BAF,Batman (JLA),DC Multiverse
2024,Plastic Man BAF,Superman (JLA - Electric Blue),DC Multiverse
2024,Plastic Man BAF,Aquaman (JLA),DC Multiverse
2024,Plastic Man BAF,Green Lantern (John Stewart),DC Multiverse
2024,Batman & Robin BAF,Batman (Clooney),DC Multiverse
2024,Batman & Robin BAF,Robin (O'Donnell),DC Multiverse
2024,Batman & Robin BAF,Batgirl (Silverstone),DC Multiverse
2024,Batman & Robin BAF,Poison Ivy (Thurman),DC Multiverse
2024,Collector Edition,Wonder Woman (Classic),DC Multiverse
2024,Collector Edition,Green Lantern (Alan Scott),DC Multiverse
2024,Collector Edition,Sinestro (Classic),DC Multiverse
2024,Collector Edition,Hawkman (Zero Hour),DC Multiverse
2024,Collector Edition,Superman (Return of Superman),DC Multiverse
2024,Collector Edition,Captain Boomerang,DC Multiverse
2024,Collector Edition,Starfire,DC Multiverse
2024,Collector Edition,Penguin (Classic),DC Multiverse
2024,Crisis Wave,Superman (Earth-2),DC Multiverse
2024,Crisis Wave,The Spectre,DC Multiverse
2024,Crisis Wave,Kid Flash,DC Multiverse
2024,Crisis Wave,Psycho Pirate,DC Multiverse
2024,Monitor BAF,Monitor,DC Multiverse
2025,Collector Edition,Blackhawk,DC Multiverse
2025,Collector Edition,Elongated Man,DC Multiverse
2025,Collector Edition,Cosmic Boy,DC Multiverse
2025,Collector Edition,Professor Pyg,DC Multiverse
2025,Collector Edition,Zatanna with Detective Chimp,DC Multiverse
2025,Platinum,Batman (Rainbow Suit),DC Multiverse
2025,Platinum,Batman (Green Suit),DC Multiverse
2025,Platinum,Mister Miracle (Gold Label),DC Multiverse
2025,Platinum,Superman (False God),DC Multiverse
2025,Platinum,Green Arrow (Longbow Hunter),DC Multiverse
2026,Green Lantern (Hal Jordan),DC Multiverse
2026,Ice (Fire & Ice),DC Multiverse
2026,Rocket Red Brigade,DC Multiverse
2026,The Flash (JLA),DC Multiverse
2026,Superman (The Authority),DC Multiverse"""
    
    # File paths
    json_file = r'c:\Code\ActionFigureTracker\Models\all_figures.json'
    backup_file = json_file + '.backup'
    
    print("Loading existing JSON...")
    existing_figures = load_existing_json(json_file)
    print(f"   Found {len(existing_figures)} existing figures")
    
    print("Parsing CSV data...")
    if csv_file_path and os.path.exists(csv_file_path):
        print(f"   Reading from file: {csv_file_path}")
        csv_data = load_csv_data(csv_file=csv_file_path)
    else:
        print("   Using embedded CSV data (file not found)")
        csv_data = load_csv_data(csv_string=csv_data_str)
    print(f"   Found {len(csv_data)} CSV entries")
    
    print("Merging data...")
    merged_figures = merge_data(existing_figures, csv_data)
    
    print(f"\nMerge complete!")
    print(f"   Total figures: {len(merged_figures)}")
    
    # Create backup
    print(f"\nCreating backup...")
    import shutil
    shutil.copy2(json_file, backup_file)
    print(f"   Backup saved to: {backup_file}")
    
    # Write merged data
    print(f"\nWriting merged JSON...")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(merged_figures, f, indent=2, ensure_ascii=False)
    
    print(f"Done! Merged data saved to: {json_file}")
    print(f"\nSummary by year:")
    year_counts = {}
    for fig in merged_figures:
        year = fig.get('year', 'Unknown')
        year_counts[year] = year_counts.get(year, 0) + 1
    # Sort years, handling both int and str types
    def year_key(y):
        if isinstance(y, int):
            return (0, y)  # Ints first
        elif y == 'Unknown':
            return (2, 0)  # Unknown last
        else:
            return (1, str(y))  # Strings in middle
    for year in sorted(year_counts.keys(), key=year_key):
        print(f"   {year}: {year_counts[year]} figures")

if __name__ == '__main__':
    main()
